from functools import lru_cache
from pydantic import BaseSettings


class Settings(BaseSettings):
    admin_username: str = "admin"
    admin_password: str = "changeme"
    access_token_expire_minutes: int = 60 * 24
    jwt_secret_key: str = "super-secret-key"
    jwt_algorithm: str = "HS256"

    database_url: str = "sqlite:///./vpn.db"
    wg_interface: str = "wg0"
    wg_conf_path: str = "/etc/wireguard/wg0.conf"
    vpn_network_cidr: str = "10.8.0.0/24"
    vpn_dns: str = "1.1.1.1, 8.8.8.8"
    server_public_endpoint: str = "vpn.example.com:51820"
    frontend_base_url: str = "https://myvpn.domain"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
