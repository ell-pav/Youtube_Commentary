from fastapi import APIRouter, Depends, HTTPException, status, Body, Security, Path
from sqlalchemy.orm import Session
from api.db.database import SessionLocal, engine
from api.db.models import User as DBUser, UserRole
from api.users.models import UserCreate, UserRead, Token, RefreshTokenRequest
from api.core.security import hash_password
from api.core.security import verify_password, create_access_token, create_refresh_token, verify_refresh_token, revoke_all_user_refresh_tokens
from api.core.security import get_current_user, oauth2_scheme
from api.core.permissions import Scope, get_user_scopes, require_scope, has_required_scope
from fastapi.security import OAuth2PasswordRequestForm, SecurityScopes
from loguru import logger
import json
from typing import Dict, Any, List, Optional

from ..db.encrypted_database import get_encrypted_db
from ..db.encrypted_services import EncryptedDataService
# Suppression des importations problématiques
# from ..models.user import User
# from ..schemas.user import UserResponse, UserLogin, UserLoginResponse
# from ..services.users import UserService
# from ..auth.jwt_handler import get_current_user
# from ..db.session import get_db
# from ..db.models import User
# from ..schemas.user_schema import UserCreate, UserResponse, UserUpdate

router = APIRouter(tags=["users"])

# Création automatique des tables
DBUser.metadata.create_all(bind=engine)

# Importer get_db depuis le module de base de données
from api.db.database import get_db


@router.post("/", response_model=UserRead)
def create_user(
    user: UserCreate, 
    db: Session = Depends(get_db), 
    current_user: DBUser = Depends(require_scope(Scope.ADMIN_WRITE.value))
):
    """
    Crée un nouvel utilisateur. 
    Requiert le scope `admin:write`.
    """
    logger.info(f"Tentative de création d'utilisateur avec l'email: {user.email} par l'administrateur: {current_user.email}")
    db_user = db.query(DBUser).filter(DBUser.email == user.email).first()
    if db_user:
        logger.warning(f"Tentative de création avec un email déjà existant: {user.email}")
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pw = hash_password(user.password)
    new_user = DBUser(
        email=user.email,
        hashed_password=hashed_pw,
        full_name=user.full_name,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.success(f"Utilisateur créé avec succès: {user.email}")
    return new_user


# Route spéciale pour créer le premier administrateur
@router.post("/first-admin", response_model=UserRead)
def create_first_admin(user: UserCreate, db: Session = Depends(get_db)):
    """
    Crée le premier administrateur du système.
    Cette route est accessible sans authentification.
    """
    # Vérifier s'il existe déjà des administrateurs
    admins = db.query(DBUser).filter(DBUser.role == UserRole.ADMINISTRATEUR).first()
    if admins:
        logger.warning(f"Tentative de création d'un premier administrateur alors qu'il en existe déjà")
        raise HTTPException(status_code=403, detail="Un administrateur existe déjà")
    
    logger.info(f"Création du premier administrateur avec l'email: {user.email}")
    db_user = db.query(DBUser).filter(DBUser.email == user.email).first()
    if db_user:
        logger.warning(f"Tentative de création avec un email déjà existant: {user.email}")
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pw = hash_password(user.password)
    new_user = DBUser(
        email=user.email,
        hashed_password=hashed_pw,
        full_name=user.full_name,
        role=UserRole.ADMINISTRATEUR  # Force le rôle administrateur
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.success(f"Premier administrateur créé avec succès: {user.email}")
    return new_user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), 
          db: Session = Depends(get_db)):
    """
    Connexion d'un utilisateur avec son email et mot de passe.
    Retourne un access_token et un refresh_token.
    """
    logger.info(f"Tentative de connexion pour l'utilisateur: {form_data.username}")
    user = db.query(DBUser).filter(DBUser.email == form_data.username).first()
    
    if not user:
        logger.warning(f"Échec de connexion - utilisateur {form_data.username} non trouvé")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    logger.debug(f"Utilisateur trouvé: {user.email}, id: {user.id}, rôle: {user.role}")
    logger.debug(f"Mot de passe fourni de longueur {len(form_data.password)}")
    logger.debug(f"Hash stocké de longueur {len(user.hashed_password)}")
    
    if not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Échec de connexion - mot de passe incorrect pour {form_data.username}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Récupérer les scopes de l'utilisateur selon son rôle
    user_scopes = get_user_scopes(user)
    logger.debug(f"Scopes attribués à l'utilisateur: {user_scopes}")
    
    # Création du access token avec les scopes
    access_token = create_access_token(
        data={"sub": user.email},
        scopes=user_scopes
    )
    
    # Création du refresh token
    refresh_token = create_refresh_token(db, user.id)
    
    logger.success(f"Connexion réussie pour l'utilisateur: {form_data.username}")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh-token", response_model=Token)
def refresh_token(
    refresh_request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Génère un nouveau access token et refresh token à partir d'un refresh token valide.
    """
    # Vérifier le refresh token
    user = verify_refresh_token(db, refresh_request.refresh_token)
    if not user:
        logger.warning(f"Tentative d'utilisation d'un refresh token invalide")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Récupérer les scopes de l'utilisateur selon son rôle
    user_scopes = get_user_scopes(user)
    
    # Créer un nouveau access token avec les scopes
    access_token = create_access_token(
        data={"sub": user.email},
        scopes=user_scopes
    )
    
    # Créer un nouveau refresh token (rotation)
    new_refresh_token = create_refresh_token(db, user.id)
    
    logger.success(f"Tokens rafraîchis avec succès pour l'utilisateur: {user.email}")
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserRead)
async def read_user_me(
    current_user: DBUser = Depends(get_current_user),
):
    """
    Return information about the current user.
    """
    # Convert the DB model to a Pydantic model
    return UserRead.from_orm(current_user)


@router.get("/", response_model=List[UserRead])
def get_users(
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(require_scope(Scope.ADMIN_READ.value))
):
    """
    Récupère tous les utilisateurs.
    Requiert le scope `admin:read`.
    """
    users = db.query(DBUser).all()
    return users


@router.delete("/data-sensibles", response_model=Dict[str, Any])
def delete_sensitive_data(
    current_user: DBUser = Depends(require_scope(Scope.SENSITIVE_DELETE.value)),
    encrypted_db: Session = Depends(get_encrypted_db)
):
    """
    Supprime les données sensibles chiffrées de l'utilisateur actuellement connecté.
    Requiert le scope `sensitive:delete`.
    """
    try:
        logger.info(f"Tentative de suppression des données sensibles pour l'utilisateur {current_user.id}")
        result = EncryptedDataService.delete_sensitive_data(current_user.id, encrypted_db)
        
        if result:
            return {"success": True, "message": "Données sensibles supprimées avec succès"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aucune donnée sensible trouvée pour cet utilisateur"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la suppression des données sensibles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Une erreur est survenue lors de la suppression des données sensibles"
        )


@router.delete("/{user_id}", response_model=Dict[str, str])
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(require_scope(Scope.ADMIN_DELETE.value))
):
    """
    Supprime un utilisateur par son ID.
    Requiert le scope `admin:delete`.
    """
    try:
        # Supprimer l'utilisateur de la base de données
        user = db.query(DBUser).filter(DBUser.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        # Révoquer tous les tokens de rafraîchissement de l'utilisateur
        revoke_all_user_refresh_tokens(db, user_id)
        
        # Supprimer l'utilisateur
        db.delete(user)
        db.commit()
        
        logger.success(f"Utilisateur {user.email} (ID: {user_id}) supprimé avec succès par {current_user.email}")
        return {"message": f"Utilisateur {user.email} supprimé avec succès"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Erreur lors de la suppression de l'utilisateur: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Une erreur est survenue lors de la suppression de l'utilisateur"
        )


@router.delete("/me", status_code=status.HTTP_200_OK)
async def delete_own_account(
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    encrypted_db: Session = Depends(get_encrypted_db)
):
    """
    Permet à un utilisateur de supprimer son propre compte.
    Cette action est irréversible et supprime également toutes les données associées à l'utilisateur.
    """
    try:
        user_id = current_user.id
        user_email = current_user.email
        
        logger.info(f"Tentative de suppression du compte utilisateur {user_id} ({user_email})")
        
        # 1. Supprimer les données sensibles de l'utilisateur si elles existent
        try:
            EncryptedDataService.delete_sensitive_data(user_id, encrypted_db)
            logger.info(f"Données sensibles supprimées pour l'utilisateur {user_id}")
        except Exception as e:
            logger.warning(f"Aucune donnée sensible trouvée ou erreur lors de la suppression pour l'utilisateur {user_id}: {str(e)}")
        
        # 2. Révoquer tous les tokens de rafraîchissement
        revoke_all_user_refresh_tokens(db, user_id)
        logger.info(f"Tous les tokens de l'utilisateur {user_id} ont été révoqués")
        
        # 3. Supprimer l'utilisateur de la base de données
        user = db.query(DBUser).filter(DBUser.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        db.delete(user)
        db.commit()
        
        logger.success(f"Compte utilisateur {user_email} (ID: {user_id}) supprimé avec succès")
        return {"success": True, "message": "Compte utilisateur supprimé avec succès"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la suppression du compte utilisateur: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Une erreur est survenue lors de la suppression du compte utilisateur"
        )


@router.post("/logout")
def logout(
    refresh_request: RefreshTokenRequest = Body(...),
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Déconnexion d'un utilisateur en révoquant son refresh token.
    """
    # Révoquer tous les refresh tokens de l'utilisateur
    revoke_all_user_refresh_tokens(db, current_user.id)
    
    logger.info(f"Déconnexion réussie pour l'utilisateur: {current_user.email}")
    return {"message": "Déconnexion réussie"}


@router.post("/logout-all")
def logout_all_devices(
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Déconnecte l'utilisateur de tous ses appareils en révoquant tous ses refresh tokens.
    """
    revoke_all_user_refresh_tokens(db, current_user.id)
    
    logger.info(f"Déconnexion de tous les appareils pour l'utilisateur: {current_user.email}")
    return {"message": "Déconnexion de tous les appareils réussie"}


@router.get("/check-admin-exists")
def check_admin_exists(db: Session = Depends(get_db)):
    """
    Vérifie s'il existe déjà un administrateur dans la base de données.
    Cette route est accessible sans authentification.
    """
    logger.info("Vérification de l'existence d'un administrateur")
    admin = db.query(DBUser).filter(DBUser.role == UserRole.ADMINISTRATEUR).first()
    return {"admin_exists": admin is not None}


@router.post("/data-sensibles", response_model=Dict[str, Any])
def store_sensitive_data(
    data: Dict[str, Any] = Body(...),
    current_user: DBUser = Depends(require_scope(Scope.SENSITIVE_WRITE.value)),
    encrypted_db: Session = Depends(get_encrypted_db)
):
    """
    Stocke les données sensibles chiffrées pour l'utilisateur actuellement connecté.
    Requiert le scope `sensitive:write`.
    """
    try:
        logger.info(f"Tentative de stockage des données sensibles pour l'utilisateur {current_user.id}")
        result = EncryptedDataService.store_sensitive_data(current_user.id, data, encrypted_db)
        
        if result:
            return {"success": True, "message": "Données sensibles stockées avec succès"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Échec du stockage des données sensibles"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors du stockage des données sensibles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Une erreur est survenue lors du stockage des données sensibles"
        )


@router.get("/data-sensibles", response_model=Dict[str, Any])
def get_sensitive_data(
    current_user: DBUser = Depends(require_scope(Scope.SENSITIVE_READ.value)),
    encrypted_db: Session = Depends(get_encrypted_db)
):
    """
    Récupère les données sensibles chiffrées de l'utilisateur actuellement connecté.
    Requiert le scope `sensitive:read`.
    """
    try:
        logger.info(f"Tentative de récupération des données sensibles pour l'utilisateur {current_user.id}")
        result = EncryptedDataService.get_sensitive_data(current_user.id, encrypted_db)
        
        if result:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aucune donnée sensible trouvée pour cet utilisateur"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des données sensibles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Une erreur est survenue lors de la récupération des données sensibles"
        )


@router.patch("/data-sensibles", response_model=Dict[str, Any])
def update_sensitive_data(
    data: Dict[str, Any] = Body(...),
    current_user: DBUser = Depends(require_scope(Scope.SENSITIVE_WRITE.value)),
    encrypted_db: Session = Depends(get_encrypted_db)
):
    """
    Met à jour partiellement les données sensibles chiffrées de l'utilisateur actuellement connecté.
    Requiert le scope `sensitive:write`.
    """
    try:
        logger.info(f"Tentative de mise à jour partielle des données sensibles pour l'utilisateur {current_user.id}")
        result = EncryptedDataService.update_partial_data(current_user.id, data, encrypted_db)
        
        if result:
            return {"success": True, "message": "Données sensibles mises à jour avec succès"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Échec de la mise à jour des données sensibles"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des données sensibles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Une erreur est survenue lors de la mise à jour des données sensibles"
        )


@router.get("/my-scopes", response_model=list[str])
def get_my_scopes(current_user: DBUser = Depends(get_current_user)):
    """
    Récupère les scopes de l'utilisateur connecté.
    
    Retourne la liste des scopes associés au rôle de l'utilisateur.
    """
    try:
        scopes = get_user_scopes(current_user)
        return scopes
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des scopes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des scopes"
        )


# Route d'inscription publique
@router.post("/register", status_code=201, response_model=UserRead)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Inscription d'un nouvel utilisateur.
    Cette route est accessible publiquement.
    """
    logger.info(f"Tentative d'inscription avec l'email: {user.email}")
    db_user = db.query(DBUser).filter(DBUser.email == user.email).first()
    if db_user:
        logger.warning(f"Tentative d'inscription avec un email déjà existant: {user.email}")
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Création du hash du mot de passe
    hashed_pw = hash_password(user.password)
    
    # Création de l'utilisateur avec le rôle UTILISATEUR par défaut
    new_user = DBUser(
        email=user.email,
        hashed_password=hashed_pw,
        full_name=user.full_name,
        role=UserRole.UTILISATEUR  # Force le rôle utilisateur pour l'inscription publique
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.success(f"Utilisateur inscrit avec succès: {user.email}")
    return new_user


# Aliaser la route login pour la rendre accessible via /token pour les tests
@router.post("/token", response_model=Token)
def token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Alias de la route login pour la compatibilité avec les tests.
    """
    return login(form_data, db)


# Ajout d'une route GET pour récupérer un utilisateur par ID
@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int = Path(..., title="ID de l'utilisateur à récupérer"),
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    """
    Récupère un utilisateur par son ID.
    Un utilisateur peut voir son propre profil.
    Un administrateur peut voir le profil de n'importe quel utilisateur.
    """
    # Vérification des droits d'accès
    if current_user.id != user_id and not has_required_scope(current_user, Scope.ADMIN_READ.value):
        logger.warning(f"Accès non autorisé: {current_user.email} essaie d'accéder au profil de l'utilisateur {user_id}")
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if user is None:
        logger.warning(f"Utilisateur avec l'id {user_id} non trouvé")
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


# Ajout d'une route PUT pour mettre à jour un utilisateur
@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    user_data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    """
    Met à jour les informations d'un utilisateur.
    Un utilisateur peut modifier son propre profil.
    Un administrateur peut modifier le profil de n'importe quel utilisateur.
    """
    # Vérification des droits d'accès
    if current_user.id != user_id and not has_required_scope(current_user, Scope.ADMIN_WRITE.value):
        logger.warning(f"Accès non autorisé: {current_user.email} essaie de modifier le profil de l'utilisateur {user_id}")
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Récupération de l'utilisateur
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if user is None:
        logger.warning(f"Utilisateur avec l'id {user_id} non trouvé")
        raise HTTPException(status_code=404, detail="User not found")
    
    # Mise à jour des champs autorisés
    if "full_name" in user_data:
        user.full_name = user_data["full_name"]
    
    if "email" in user_data:
        # Vérifier si l'email est déjà utilisé par un autre utilisateur
        existing_user = db.query(DBUser).filter(DBUser.email == user_data["email"]).first()
        if existing_user and existing_user.id != user_id:
            raise HTTPException(status_code=400, detail="Email already registered")
        user.email = user_data["email"]
    
    # Si l'utilisateur est admin, il peut changer le rôle
    if has_required_scope(current_user, Scope.ADMIN_WRITE.value) and "role" in user_data:
        try:
            user.role = UserRole(user_data["role"])
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid role")
    
    db.commit()
    db.refresh(user)
    
    logger.success(f"Utilisateur {user_id} mis à jour avec succès")
    return user 