import json
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger
from api.db.encrypted_database import EncryptedUserData, EncryptionManager
from typing import Dict, Any, Optional

# Initialisation du gestionnaire de chiffrement
encryption_manager = EncryptionManager()

class EncryptedDataService:
    """Service pour gérer les opérations CRUD sur les données chiffrées"""
    
    @staticmethod
    def store_sensitive_data(user_id: int, data: dict, db: Session) -> bool:
        """
        Stocke les données sensibles chiffrées pour un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            data: Données à chiffrer et stocker
            db: Session de base de données
            
        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        try:
            # Vérifier si la table existe et créer si nécessaire
            from api.db.encrypted_database import init_encrypted_db
            try:
                init_encrypted_db()
            except Exception as e:
                logger.error(f"Erreur lors de l'initialisation de la base de données: {e}")
                return False
            
            # Vérifier si l'utilisateur a déjà des données stockées
            existing_data = db.query(EncryptedUserData).filter(
                EncryptedUserData.user_id == user_id
            ).first()
            
            if existing_data:
                logger.warning(f"Des données sensibles existent déjà pour l'utilisateur {user_id}. Suppression avant nouvelle insertion.")
                db.delete(existing_data)
                db.commit()
            
            # Chiffrer les données avec Fernet
            encrypted_data = encryption_manager.encrypt_dict(data)
            
            # Créer et enregistrer l'entrée dans la base de données
            new_data = EncryptedUserData(
                user_id=user_id,
                encrypted_data=encrypted_data
            )
            
            db.add(new_data)
            db.commit()
            
            logger.info(f"Données sensibles stockées avec succès pour l'utilisateur {user_id}")
            return True
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Erreur SQLAlchemy lors du stockage des données sensibles: {str(e)}")
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"Erreur inattendue lors du stockage des données sensibles: {str(e)}")
            return False
    
    @staticmethod
    def get_sensitive_data(user_id: int, db: Session) -> Optional[dict]:
        """
        Récupère et déchiffre les données sensibles d'un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            db: Session de base de données
            
        Returns:
            dict: Données déchiffrées ou None si aucune donnée n'est trouvée
        """
        try:
            # Récupérer les données chiffrées pour cet utilisateur
            user_data = db.query(EncryptedUserData).filter(
                EncryptedUserData.user_id == user_id
            ).first()
            
            if not user_data:
                logger.warning(f"Aucune donnée sensible trouvée pour l'utilisateur {user_id}")
                return None
            
            # Déchiffrer les données
            decrypted_data = encryption_manager.decrypt_dict(user_data.encrypted_data)
            
            logger.info(f"Données sensibles récupérées avec succès pour l'utilisateur {user_id}")
            return decrypted_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données sensibles: {str(e)}")
            return None
    
    @staticmethod
    def delete_sensitive_data(user_id: int, db: Session) -> bool:
        """
        Supprime les données sensibles d'un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            db: Session de base de données
            
        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        try:
            # Récupérer les données chiffrées de l'utilisateur
            db_encrypted_data = db.query(EncryptedUserData).filter(
                EncryptedUserData.user_id == user_id
            ).first()
            
            if not db_encrypted_data:
                logger.warning(f"Aucune donnée sensible trouvée pour l'utilisateur {user_id}")
                return False
            
            # Supprimer l'enregistrement
            db.delete(db_encrypted_data)
            db.commit()
            
            logger.info(f"Données sensibles supprimées avec succès pour l'utilisateur {user_id}")
            return True
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Erreur SQLAlchemy lors de la suppression des données sensibles: {str(e)}")
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"Erreur inattendue lors de la suppression des données sensibles: {str(e)}")
            return False
    
    @staticmethod
    def update_partial_data(user_id: int, new_data: dict, db: Session) -> bool:
        """
        Met à jour partiellement les données sensibles d'un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            new_data: Nouvelles données à fusionner avec les données existantes
            db: Session de base de données
            
        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        try:
            # Récupérer les données existantes
            existing_data = EncryptedDataService.get_sensitive_data(user_id, db)
            
            if not existing_data:
                logger.warning(f"Aucune donnée sensible trouvée pour l'utilisateur {user_id}")
                return False
            
            # Fusionner les données existantes avec les nouvelles données
            updated_data = {**existing_data, **new_data}
            
            # Stocker les données mises à jour
            result = EncryptedDataService.store_sensitive_data(user_id, updated_data, db)
            
            if result:
                logger.info(f"Données sensibles mises à jour avec succès pour l'utilisateur {user_id}")
                return True
            else:
                logger.error(f"Échec de la mise à jour des données sensibles pour l'utilisateur {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des données sensibles: {str(e)}")
            return False 