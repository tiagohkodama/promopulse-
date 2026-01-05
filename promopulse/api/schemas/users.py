from pydantic import BaseModel, EmailStr


class UserCreatePayload(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr


class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr

    class Config:
        from_attributes = True  # For Pydantic v2 compatibility with SQLAlchemy