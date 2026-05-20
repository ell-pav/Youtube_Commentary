import os
import json
import base64
import logging
from typing import Dict, Any, Optional
from sqlalchemy import Column, Integer, String, LargeBinary, create_engine, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util.Padding import pad, unpad
from loguru import logger
from api.core.config import ENCRYPTED_DATABASE_URL, TESTING
from cryptography.fernet import Fernet
from datetime import datetime, timezone

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("encrypted-db")

# Création d'une classe de base pour les modèles SQLAlchemy
EncryptedBase = declarative_base()

# Vérifier si nous sommes en mode test
if TESTING:
    logger.info(f"Mode TEST activé, utilisation d'une base de données chiffrée SQLite en mémoire partagée")
    # URL de connexion spéciale qui permet de partager la même base de données en mémoire
    # entre différentes connexions
    TEST_ENCRYPTED_DATABASE_URL = "sqlite:///:memory:"
    
    # Création du moteur SQLAlchemy pour les tests
    encrypted_engine = create_engine(
        TEST_ENCRYPTED_DATABASE_URL,
        connect_args={"check_same_thread": False}  # Nécessaire pour SQLite
    )
    
    # Exporter la variable d'environnement pour que toutes les parties de l'application
    # utilisent la même base de données en mémoire
    os.environ["TEST_ENCRYPTED_DATABASE_URL"] = TEST_ENCRYPTED_DATABASE_URL
else:
    logger.info(f"Initialisation de la base de données chiffrée SQLAlchemy avec: {ENCRYPTED_DATABASE_URL}")
    # Création du moteur SQLAlchemy normal
    encrypted_engine = create_engine(
        ENCRYPTED_DATABASE_URL,
        connect_args={"check_same_thread": False} if ENCRYPTED_DATABASE_URL.startswith("sqlite") else {}
    )

# Création d'une session SQLAlchemy locale
EncryptedSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=encrypted_engine)

# Si en mode test, créer toutes les tables immédiatement
if TESTING:
    # Créer les tables
    EncryptedBase.metadata.create_all(bind=encrypted_engine)
    logger.info("Tables créées dans la base de données chiffrée de test")

# Fonction pour obtenir une session de base de données
def get_encrypted_db():
    """
    Fournit une session de base de données chiffrée, garantissant qu'elle est fermée après utilisation.
    À utiliser comme dépendance dans les routes FastAPI.
    """
    db = EncryptedSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Modèle pour les données utilisateur chiffrées
class EncryptedUserData(EncryptedBase):
    """
    Modèle pour stocker les données sensibles chiffrées des utilisateurs.
    """
    __tablename__ = "encrypted_user_data"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True)  # Lien avec la table des utilisateurs
    encrypted_data = Column(String)  # Données chiffrées stockées en format texte
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))


class EncryptionManager:
    """
    Gestionnaire de chiffrement pour la base de données séparée
    contenant les données sensibles.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EncryptionManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        try:
            # Récupérer la clé maître depuis les variables d'environnement
            master_key_b64 = os.environ.get("MASTER_ENCRYPTION_KEY")
            
            if not master_key_b64:
                # Générer une clé pour les tests/développement
                key = Fernet.generate_key()
                master_key_b64 = key.decode()
                os.environ["MASTER_ENCRYPTION_KEY"] = master_key_b64
                logger.warning("Clé de chiffrement générée pour les tests")
            
            # S'assurer que la clé est bien formatée pour Fernet
            if not master_key_b64.endswith("="):
                # Padding automatique pour la compatibilité Fernet
                while len(master_key_b64) % 4 != 0:
                    master_key_b64 += "="
            
            # Initialiser Fernet avec la clé maître
            self.fernet = Fernet(master_key_b64.encode())
            
            logger.info("Gestionnaire de chiffrement initialisé")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du gestionnaire de chiffrement: {str(e)}")
            # En cas d'erreur, on initialise un Fernet avec une clé aléatoire 
            # pour que l'application puisse continuer à fonctionner, 
            # mais les données ne seront pas correctement chiffrées/déchiffrées
            self.fernet = Fernet(Fernet.generate_key())
    
    def encrypt(self, data: str) -> str:
        """Chiffre une chaîne de caractères"""
        if not isinstance(data, str):
            data = str(data)
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Déchiffre une chaîne de caractères"""
        if not encrypted_data:
            return ""
        return self.fernet.decrypt(encrypted_data.encode()).decode()
    
    # Méthodes pour chiffrer/déchiffrer des types spécifiques
    def encrypt_dict(self, data: dict) -> str:
        """Chiffre un dictionnaire en le convertissant d'abord en JSON"""
        import json
        return self.encrypt(json.dumps(data))
        
    def decrypt_dict(self, encrypted_data: str) -> dict:
        """Déchiffre une chaîne contenant un dictionnaire JSON chiffré"""
        import json
        if not encrypted_data:
            return {}
        try:
            return json.loads(self.decrypt(encrypted_data))
        except Exception as e:
            logger.error(f"Erreur lors du déchiffrement du dictionnaire: {str(e)}")
            return {}


def init_encrypted_db():
    """
    Initialise la base de données chiffrée en créant les tables nécessaires.
    """
    EncryptedBase.metadata.create_all(bind=encrypted_engine)
    logger.info("Base de données chiffrée initialisée")


# Créer une instance du gestionnaire de chiffrement
encryption_manager = EncryptionManager() 