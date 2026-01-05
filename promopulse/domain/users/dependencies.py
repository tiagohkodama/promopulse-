from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from promopulse.db.session import get_async_session
from promopulse.core.security import get_encryption_service, EncryptionService
from promopulse.infrastructure.users.repository import UserRepository
from promopulse.domain.users.service import UserService


def get_user_repository(
    session: AsyncSession = Depends(get_async_session)
) -> UserRepository:
    """FastAPI dependency to get UserRepository instance."""
    return UserRepository(session)


def get_user_service(
    repository: UserRepository = Depends(get_user_repository),
    encryption_service: EncryptionService = Depends(get_encryption_service),
) -> UserService:
    """FastAPI dependency to get UserService instance."""
    return UserService(repository, encryption_service)
