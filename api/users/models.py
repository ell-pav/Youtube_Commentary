from pydantic import BaseModel
from api.db.models import UserRole
from typing import Optional, List


class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    role: UserRole = UserRole.UTILISATEUR


class UserRead(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    
    class Config:
        from_attributes = True
        
    def dict(self, *args, **kwargs):
        """Sérialise correctement l'énumération role en chaîne"""
        d = super().dict(*args, **kwargs)
        if isinstance(d["role"], UserRole):
            d["role"] = d["role"].value
        return d


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    token_type: Optional[str] = None
    scopes: Optional[List[str]] = []


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserScopes(BaseModel):
    scopes: List[str]
