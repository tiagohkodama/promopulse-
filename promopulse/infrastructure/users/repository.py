import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from promopulse.db.models.user import User


logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for User database operations."""
    
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self, 
        *, 
        encrypted_email: str, 
        full_name: str,
        encrypted_phone: Optional[str] = None
    ) -> User:
        """
        Create a new user in the database.
        
        Args:
            encrypted_email: The encrypted email address
            full_name: The user's full name
            encrypted_phone: Optional encrypted phone number
            
        Returns:
            The created User instance
            
        Raises:
            IntegrityError: If there's a database constraint violation
        """
        user = User(
            encrypted_email=encrypted_email,
            full_name=full_name,
            encrypted_phone=encrypted_phone,
        )
        
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        
        logger.info(
            f"User created successfully with id={user.id}",
            extra={"correlation_id": "-"}
        )
        
        return user

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get a user by ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def exists_by_encrypted_email(self, encrypted_email: str) -> bool:
        """Check if a user exists with the given encrypted email."""
        result = await self.session.execute(
            select(User.id).where(User.encrypted_email == encrypted_email)
        )
        return result.scalar_one_or_none() is not None
