from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=72)
    full_name: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
