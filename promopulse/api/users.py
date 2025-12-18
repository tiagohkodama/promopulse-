import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError

from promopulse.api.schemas.users import UserCreatePayload, UserOut
from promopulse.domain.users.service import UserService, UserAlreadyExistsError
from promopulse.domain.users.dependencies import get_user_service
router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/users", summary="Create a user", response_model=UserOut)
async def create_user(
    payload: UserCreatePayload,
    user_service: UserService = Depends(get_user_service),
):
    """
    Create a new user.

    - Validates input data
    - Applies business logic (name composition, encryption)
    - Persists to database
    - Returns user data with original email
    """
    try:
        user, original_email = await user_service.create_user(payload)

        return UserOut(
            id=user.id,
            full_name=user.full_name,
            email=original_email
        )
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="User with this email already exists"
        )
    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=409,
            detail="User with this email already exists"
        )
    except Exception as e:
        logger.error(
            f"Unexpected error creating user: {str(e)}",
            extra={"correlation_id": "-"}
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@router.get("/users/{user_id}", summary="Get user by ID", response_model=UserOut)
async def get_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
):
    """Get a user by ID."""
    result = await user_service.get_user_by_id(user_id)

    if not result:
        raise HTTPException(status_code=404, detail="User not found")

    user, decrypted_email = result
    return UserOut(
        id=user.id,
        full_name=user.full_name,
        email=decrypted_email
    )
