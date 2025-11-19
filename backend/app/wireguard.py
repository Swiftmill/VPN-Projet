import base64
import ipaddress
import os
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import qrcode

from .config import get_settings

settings = get_settings()


class WireGuardManager:
    def __init__(self) -> None:
        self.interface = settings.wg_interface
        self.conf_path = Path(settings.wg_conf_path)

    def _run(self, *args: str) -> str:
        try:
            result = subprocess.run(args, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as exc:  # noqa: BLE001
            raise RuntimeError(exc.stderr.strip() or "WireGuard command failed") from exc

    def generate_private_key(self) -> str:
        return self._run("wg", "genkey")

    def generate_public_key(self, private_key: str) -> str:
        proc = subprocess.run(["wg", "pubkey"], input=f"{private_key}\n", text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return proc.stdout.strip()

    def generate_preshared_key(self) -> str:
        return self._run("wg", "genpsk")

    def get_server_public_key(self) -> Optional[str]:
        try:
            return self._run("wg", "show", self.interface, "public-key")
        except Exception:  # noqa: BLE001
            return None

    def get_status(self) -> dict:
        status = {
            "interface": self.interface,
            "is_running": False,
            "public_key": None,
            "listen_port": None,
            "peers_count": 0,
            "latest_handshake": None,
        }
        try:
            dump = self._run("wg", "show", self.interface)
        except Exception:
            return status

        status["is_running"] = True
        status["public_key"] = self.get_server_public_key()
        listen_match = re.search(r"listening port:\s*(\d+)", dump)
        if listen_match:
            status["listen_port"] = int(listen_match.group(1))
        handshake_match = re.findall(r"latest handshake: ([^\n]+)", dump)
        if handshake_match:
            status["latest_handshake"] = handshake_match[-1]
            status["peers_count"] = len(handshake_match)
        return status

    def assign_ip(self, existing_ips: list[str]) -> str:
        network = ipaddress.ip_network(settings.vpn_network_cidr)
        used = {ipaddress.ip_address(ip.split("/")[0]) for ip in existing_ips}
        for host in network.hosts():
            if host == network.network_address + 1:  # skip gateway
                continue
            if host not in used:
                prefix = 32 if isinstance(host, ipaddress.IPv4Address) else 128
                return f"{host}/{prefix}"
        raise RuntimeError("No available IP addresses in the VPN network")

    def append_peer(self, name: str, public_key: str, preshared_key: str, allowed_ip: str) -> None:
        comment = f"\n# {name} - created {datetime.utcnow().isoformat()}\n"
        peer_block = (
            f"[Peer]\n"
            f"PublicKey = {public_key}\n"
            f"PresharedKey = {preshared_key}\n"
            f"AllowedIPs = {allowed_ip}\n"
        )
        with self.conf_path.open("a", encoding="utf-8") as config_file:
            config_file.write(comment)
            config_file.write(peer_block)

        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as tmp:
            tmp.write(peer_block)
            tmp_path = tmp.name
        try:
            self._run("wg", "addconf", self.interface, tmp_path)
        finally:
            os.unlink(tmp_path)

    def remove_peer(self, public_key: str) -> None:
        try:
            self._run("wg", "set", self.interface, "peer", public_key, "remove")
        except RuntimeError:
            pass

        if not self.conf_path.exists():
            return
        contents = self.conf_path.read_text(encoding="utf-8")
        pattern = re.compile(rf"\n?#.*?\n\[Peer\]\nPublicKey\s*=\s*{re.escape(public_key)}.*?(?=\n#|$)", re.S)
        new_contents = re.sub(pattern, "\n", contents)
        self.conf_path.write_text(new_contents.strip() + "\n", encoding="utf-8")

    def create_client_config(self, name: str, client_ip: str, client_private_key: str, client_public_key: str, preshared_key: str) -> str:
        server_public_key = self.get_server_public_key() or ""
        config = f"""[Interface]
PrivateKey = {client_private_key}
Address = {client_ip}
DNS = {settings.vpn_dns}

[Peer]
PublicKey = {server_public_key}
PresharedKey = {preshared_key}
AllowedIPs = 0.0.0.0/0
Endpoint = {settings.server_public_endpoint}
PersistentKeepalive = 25
"""
        return config

    def generate_qrcode_b64(self, config_text: str) -> str:
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L)
        qr.add_data(config_text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            img.save(tmp.name)
            tmp.seek(0)
            data = tmp.read()
        os.unlink(tmp.name)
        return base64.b64encode(data).decode()


wireguard_manager = WireGuardManager()
