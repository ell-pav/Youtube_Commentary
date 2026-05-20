import os
from dotenv import load_dotenv
from datetime import timedelta
from loguru import logger

# Chargement des variables d'environnement
load_dotenv()

# Paramètres généraux
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

# Configuration de base de données
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sqlite.db")
ENCRYPTED_DATABASE_URL = os.getenv("ENCRYPTED_DATABASE_URL", "sqlite:///./encrypted.db")

# Mode test (false par défaut)
# Force à TRUE si l'environnement de test est détecté
TESTING = os.getenv("TESTING", "false").lower() == "true" or "pytest" in os.sys.modules

# Si en mode test, utiliser une base de données en mémoire
if TESTING:
    logger.info("Mode TEST activé, utilisation de bases de données en mémoire")
    DATABASE_URL = "sqlite:///:memory:"
    ENCRYPTED_DATABASE_URL = "sqlite:///:memory:"


def get_token_expiration():
    return timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)


def get_refresh_token_expiration():
    return timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)