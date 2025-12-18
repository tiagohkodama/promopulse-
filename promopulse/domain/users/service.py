import logging
from typing import Optional

from promopulse.api.schemas.users import UserCreatePayload
from promopulse.core.security import EncryptionService
from promopulse.infrastructure.users.repository import UserRepository
from promopulse.db.models.user import User


logger = logging.getLogger(__name__)


class UserAlreadyExistsError(Exception):
    """Raised when attempting to create a user with an email that already exists."""
    pass


class UserService:
    """Service for user business logic."""
    
    def __init__(self, repository: UserRepository, encryption_service: EncryptionService):
        self.repository = repository
        self.encryption_service = encryption_service

    def _compose_full_name(self, first_name: str, last_name: str) -> str:
        """
        Compose full name from first and last name.
        
        Args:
            first_name: User's first name
            last_name: User's last name
            
        Returns:
            Composed full name, properly trimmed
        """
        return f"{first_name} {last_name}".strip()

    async def create_user(
        self, 
        payload: UserCreatePayload,
        phone: Optional[str] = None
    ) -> tuple[User, str]:
        """
        Create a new user with business logic applied.
        
        Args:
            payload: User creation data
            phone: Optional phone number
            
        Returns:
            Tuple of (created User instance, original plaintext email)
            
        Raises:
            UserAlreadyExistsError: If email already exists (when uniqueness is enforced)
        """
        # Apply business rules
        full_name = self._compose_full_name(payload.first_name, payload.last_name)
        
        # Encrypt sensitive data
        encrypted_email = self.encryption_service.encrypt(payload.email)
        encrypted_phone = self.encryption_service.encrypt(phone) if phone else None
        
        logger.info(
            f"Creating user with email={payload.email}, full_name={full_name}",
            extra={"correlation_id": "-"}
        )
        
        # Note: If you need email uniqueness, you'd check here using a hash-based approach
        # since encrypted emails are non-deterministic with Fernet
        
        try:
            user = await self.repository.create(
                encrypted_email=encrypted_email,
                full_name=full_name,
                encrypted_phone=encrypted_phone,
            )
            return user, payload.email
        except Exception as e:
            logger.error(
                f"Failed to create user: {str(e)}",
                extra={"correlation_id": "-"}
            )
            raise

    async def get_user_by_id(self, user_id: int) -> Optional[tuple[User, str]]:
        """
        Get user by ID and decrypt email.
        
        Returns:
            Tuple of (User instance, decrypted email) or None if not found
        """
        user = await self.repository.get_by_id(user_id)
        if not user:
            return None
            
        decrypted_email = self.encryption_service.decrypt(user.encrypted_email)
        return user, decrypted_email
