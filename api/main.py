from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from api.users.routes import router as user_router
from loguru import logger
from api.db.database import engine, Base
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator
import sys
import os
import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware

# Configuration du logging standard Python
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        # Ajouter un handler de fichier pour le logging standard
        logging.FileHandler(os.path.join("logs", "python_std.log"), mode='a', encoding='utf-8')
    ]
)
# Activer les logs pour le module de sécurité
logging.getLogger('api.core.security').setLevel(logging.DEBUG)

# Configuration Loguru améliorée
log_path = "logs"
if not os.path.exists(log_path):
    os.makedirs(log_path)

# Réinitialiser complètement la configuration de loguru
logger.remove()  # Supprimer tous les handlers existants

# Ajouter un handler pour la console
logger.add(
    sys.stderr, 
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True
)

# Ajouter un handler pour les fichiers
logger.add(
    os.path.join(log_path, "app_{time}.log"), 
    rotation="10 MB",  # Rotation basée sur la taille plutôt que le temps
    retention="1 week",
    compression="zip",  # Compresser les anciens logs
    level="DEBUG",
    backtrace=True,  # Afficher les traces d'erreur complètes
    diagnose=True,   # Ajouter des informations de diagnostic
    enqueue=True,    # File d'attente des logs pour améliorer les performances
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
)

# Ajouter un fichier de log séparé pour les requêtes HTTP
logger.add(
    os.path.join(log_path, "requests_{time}.log"),
    rotation="10 MB",
    retention="1 week",
    level="INFO",
    filter=lambda record: record["extra"].get("request_id") is not None,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {extra[request_id]} | {extra[method]} {extra[url]} | {message}"
)

# Journaliser le démarrage du système de logging
logger.info("Système de journalisation initialisé")

# Middleware pour logguer les requêtes HTTP
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = f"req-{time.time()}"
        method = request.method
        url = request.url.path
        query = request.url.query
        if query:
            url = f"{url}?{query}"
        
        logger_with_context = logger.bind(
            request_id=request_id,
            method=method,
            url=url
        )
        
        logger_with_context.info(f"Début de requête")
        
        start_time = time.time()
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            logger_with_context.info(f"Fin de requête - statut {response.status_code} - durée {process_time:.4f}s")
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger_with_context.error(f"Erreur lors du traitement de la requête - {str(e)} - durée {process_time:.4f}s")
            raise

app = FastAPI()

# Ajouter le middleware de logging
app.add_middleware(LoggingMiddleware)

# Ajouter middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Pour le développement
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ajout Prometheus
Instrumentator().instrument(app).expose(app)

# Inclusion des routes des utilisateurs
app.include_router(
    user_router,
    prefix="/users",
    tags=["users"]
)

@app.get("/")
def read_root():
    logger.info("Accès à la racine de l'API")
    return {"message": "Hello Modular World"}

@app.get("/health")
def health_check():
    logger.info("Vérification de santé effectuée")
    return {"status": "healthy"}

@app.on_event("startup")
async def lifespan():
    """
    Cette fonction est exécutée au démarrage de l'application.
    Elle initialise les ressources nécessaires comme les connexions à la base de données.
    """
    logger.info("Démarrage de l'application...")
    
    # Vérifier la connexion à la base de données principale
    from api.db.database import engine, Base
    try:
        # Créer toutes les tables si elles n'existent pas
        Base.metadata.create_all(bind=engine)
        logger.info("Base de données principale connectée avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de la connexion à la base de données principale: {str(e)}")
        raise e
    
    # Vérifier la connexion à la base de données chiffrée
    from api.db.encrypted_database import EncryptedBase, encrypted_engine
    try:
        # Créer toutes les tables si elles n'existent pas
        EncryptedBase.metadata.create_all(bind=encrypted_engine)
        logger.info("Base de données chiffrée connectée avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de la base de données chiffrée: {str(e)}")


@app.on_event("shutdown")
async def shutdown():
    """
    Cette fonction est exécutée à l'arrêt de l'application.
    Elle libère les ressources comme les connexions à la base de données.
    """
    logger.info("Fermeture de la connexion à la base de données...")
    logger.info("Arrêt de l'application...")
