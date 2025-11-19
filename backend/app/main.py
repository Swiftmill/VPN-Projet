from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models
from .config import get_settings
from .database import engine, get_db
from .models import Client
from .schemas import ClientCreate, ClientResponse, LoginRequest, ServerStatus, TokenResponse
from .security import create_access_token, get_current_user
from .wireguard import wireguard_manager

settings = get_settings()
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Self-Hosted WireGuard VPN API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_base_url, "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    if payload.username != settings.admin_username or payload.password != settings.admin_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(payload.username)
    return TokenResponse(access_token=token)


@app.get("/server/status", response_model=ServerStatus)
def get_server_status(_: str = Depends(get_current_user)) -> ServerStatus:
    return ServerStatus(**wireguard_manager.get_status())


@app.get("/clients", response_model=list[ClientResponse])
def list_clients(_: str = Depends(get_current_user), db: Session = Depends(get_db)):
    clients = db.query(Client).all()
    return clients


@app.post("/clients", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client(
    payload: ClientCreate,
    _: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        private_key = wireguard_manager.generate_private_key()
        public_key = wireguard_manager.generate_public_key(private_key)
        preshared_key = wireguard_manager.generate_preshared_key()
        existing_ips = [client.ip_address for client in db.query(Client).all()]
        assigned_ip = wireguard_manager.assign_ip(existing_ips)
        wireguard_manager.append_peer(payload.name, public_key, preshared_key, assigned_ip)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    client = Client(
        name=payload.name,
        ip_address=assigned_ip,
        private_key=private_key,
        public_key=public_key,
        preshared_key=preshared_key,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@app.delete("/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_id: int, _: str = Depends(get_current_user), db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    wireguard_manager.remove_peer(client.public_key)
    db.delete(client)
    db.commit()
    return None


@app.get("/clients/{client_id}/config")
def download_config(client_id: int, _: str = Depends(get_current_user), db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    config_text = wireguard_manager.create_client_config(
        client.name,
        client.ip_address,
        client.private_key,
        client.public_key,
        client.preshared_key,
    )
    return {"config": config_text}


@app.get("/clients/{client_id}/qrcode")
def client_qrcode(client_id: int, _: str = Depends(get_current_user), db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    config_text = wireguard_manager.create_client_config(
        client.name,
        client.ip_address,
        client.private_key,
        client.public_key,
        client.preshared_key,
    )
    qr_b64 = wireguard_manager.generate_qrcode_b64(config_text)
    return {"qrcode": qr_b64}
