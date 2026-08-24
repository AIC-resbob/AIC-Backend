from pydantic import BaseModel, Field
from typing import Optional

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str

class UserResponse(BaseModel):
    id: int
    username: str
    is_active: bool

    class Config:
        from_attributes = True
class LogoutRequest(BaseModel):
    user_id: int = Field(..., description="ID of the user to log out / invalidate")
class MessageResponse(BaseModel):
    message: str