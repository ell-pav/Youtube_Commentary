from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from api.core.config import DATABASE_URL, TESTING
from loguru import logger
import os

# Vérifier si nous sommes en mode test
if TESTING:
    # En mode test, nous utilisons une URL de base de données provenant de l'environnement
    # ce qui permet aux tests de spécifier leur propre base de données si nécessaire
    logger.info(f"Mode TEST activé, utilisation d'une base de données de test")
    TEST_DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///:memory:")
    logger.info(f"URL de la base de données de test: {TEST_DATABASE_URL}")
    
    # Création du moteur SQLAlchemy pour les tests
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}  # Nécessaire pour SQLite
    )
else:
    logger.info(f"Initialisation de la base de données SQLAlchemy avec: {DATABASE_URL}")
    # Création du moteur SQLAlchemy normal
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
    )

# Création d'une session SQLAlchemy locale
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Création d'une classe de base pour les modèles SQLAlchemy
Base = declarative_base()

# Si en mode test, créer toutes les tables immédiatement
if TESTING:
    # Créer les tables
    Base.metadata.create_all(bind=engine)
    logger.info("Tables créées dans la base de données de test")

# Fonction pour obtenir une session de base de données
def get_db():
    """
    Fournit une session de base de données, garantissant qu'elle est fermée après utilisation.
    À utiliser comme dépendance dans les routes FastAPI.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
