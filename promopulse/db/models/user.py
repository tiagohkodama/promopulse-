from sqlalchemy import Column, Integer, String, DateTime, func

from .base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    encrypted_email = Column(String(512), nullable=False)
    encrypted_phone = Column(String(512), nullable=True)
    full_name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
