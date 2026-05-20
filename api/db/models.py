from sqlalchemy import Column, Integer, String, Boolean, Enum as SQLEnum, DateTime, ForeignKey, UniqueConstraint
import enum
from datetime import datetime, timezone
from api.db.database import Base

class UserRole(enum.Enum):
    ADMINISTRATEUR = "ADMINISTRATEUR"
    UTILISATEUR = "UTILISATEUR"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    role = Column(SQLEnum(UserRole))
    
    # Ajouter une contrainte d'unicité explicite pour email
    __table_args__ = (
        UniqueConstraint('email', name='uix_user_email'),
    )
    
    def __str__(self):
        """Représentation en chaîne de l'utilisateur"""
        return f"User(id={self.id}, email={self.email}, full_name={self.full_name}, role={self.role})"
    
    def __repr__(self):
        """Représentation pour le débogage"""
        return f"User(id={self.id}, email='{self.email}', full_name='{self.full_name}', role={self.role})"


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    revoked = Column(Boolean, default=False)
    
    @property
    def is_valid(self):
        """Vérifie si le token est valide (non expiré et non révoqué)"""
        now = datetime.now(timezone.utc)
        # Ajouter le fuseau horaire UTC à expires_at s'il n'en a pas
        expires_at = self.expires_at
        if expires_at and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return not self.revoked and now < expires_at


class TokenBlacklist(Base):
    """Modèle pour stocker les JWT en liste noire (révoqués)"""
    __tablename__ = "token_blacklist"
    
    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String, unique=True, index=True)  # JWT ID unique
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    @classmethod
    def is_blacklisted(cls, db, jti):
        """Vérifie si un token est en liste noire par son JTI"""
        return db.query(cls).filter(cls.jti == jti).first() is not None
