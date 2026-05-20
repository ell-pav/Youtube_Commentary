from enum import Enum, auto
from typing import List, Dict, Set, Optional
from fastapi import Depends, HTTPException, status
from api.db.models import UserRole
from api.core.security import get_current_user
from api.db.models import User as DBUser

# Définition des scopes de permission
class Scope(str, Enum):
    # Scopes admin
    ADMIN_READ = "admin:read"
    ADMIN_WRITE = "admin:write"
    ADMIN_DELETE = "admin:delete"
    
    # Scopes utilisateur
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    
    # Scopes pour les données sensibles
    SENSITIVE_READ = "sensitive:read"
    SENSITIVE_WRITE = "sensitive:write"
    SENSITIVE_DELETE = "sensitive:delete"


# Permissions par rôle
ROLE_SCOPES: Dict[UserRole, List[Scope]] = {
    UserRole.ADMINISTRATEUR: [
        Scope.ADMIN_READ, Scope.ADMIN_WRITE, Scope.ADMIN_DELETE,
        Scope.USER_READ, Scope.USER_WRITE, Scope.USER_DELETE,
        Scope.SENSITIVE_READ, Scope.SENSITIVE_WRITE, Scope.SENSITIVE_DELETE
    ],
    UserRole.UTILISATEUR: [
        Scope.USER_READ,
        Scope.SENSITIVE_READ, Scope.SENSITIVE_WRITE, Scope.SENSITIVE_DELETE
    ]
}


def get_user_scopes(user: DBUser) -> List[str]:
    """Récupère les scopes associés au rôle de l'utilisateur"""
    return [scope.value for scope in ROLE_SCOPES.get(user.role, [])]


def has_required_scope(user: DBUser, required_scope: str) -> bool:
    """Vérifie si l'utilisateur possède le scope requis"""
    user_scopes = get_user_scopes(user)
    return required_scope in user_scopes


# Dépendances pour vérifier les scopes
def require_scope(required_scope: str):
    """
    Dépendance FastAPI pour vérifier qu'un utilisateur a le scope requis.
    À utiliser avec Depends() dans les routes.
    
    Note: Cette fonction peut être remplacée (mockée) lors des tests
    pour contourner l'authentification.
    """
    def scope_dependency(current_user: DBUser = Depends(get_current_user)) -> DBUser:
        if not has_required_scope(current_user, required_scope):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission refusée. Le scope '{required_scope}' est requis."
            )
        return current_user
    
    return scope_dependency


# Décorateur de fonction pour vérifier les scopes (alternative aux Depends)
def require_scopes(required_scopes: List[str]):
    """
    Décorateur pour vérifier que l'utilisateur a au moins un des scopes requis.
    Exemple d'utilisation:
        @require_scopes([Scope.ADMIN_READ.value, Scope.USER_READ.value])
        def my_function(user):
            ...
    """
    def decorator(func):
        def wrapper(user: DBUser, *args, **kwargs):
            user_scopes = get_user_scopes(user)
            if not any(scope in user_scopes for scope in required_scopes):
                scopes_str = ", ".join(required_scopes)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission refusée. Au moins un des scopes suivants est requis: {scopes_str}"
                )
            return func(user, *args, **kwargs)
        return wrapper
    return decorator 