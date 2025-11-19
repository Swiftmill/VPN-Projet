from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


class ClientCreate(BaseModel):
    name: str


class ClientResponse(BaseModel):
    id: int
    name: str
    ip_address: str
    public_key: str
    created_at: datetime

    class Config:
        orm_mode = True


class ServerStatus(BaseModel):
    interface: str
    is_running: bool
    public_key: Optional[str]
    listen_port: Optional[int]
    peers_count: int
    latest_handshake: Optional[str]
