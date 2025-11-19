#!/usr/bin/env bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "This installer must be run as root" >&2
  exit 1
fi

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_DIR="/opt/vpn-dashboard"
BACKEND_DIR="$INSTALL_DIR/backend"
FRONTEND_DIR="$INSTALL_DIR/frontend"
ENV_FILE="$INSTALL_DIR/.env"
WG_CONF="/etc/wireguard/wg0.conf"
WG_INTERFACE="wg0"
VPN_NETWORK="10.8.0.0/24"
VPN_ADDRESS="10.8.0.1/24"
LISTEN_PORT=51820

apt-get update
apt-get install -y wireguard wireguard-tools python3 python3-venv python3-pip nginx nodejs npm sqlite3 qrencode

cat <<SYSCTL >/etc/sysctl.d/99-wireguard-forwarding.conf
net.ipv4.ip_forward=1
net.ipv6.conf.all.forwarding=1
SYSCTL
sysctl --system

mkdir -p /etc/wireguard
if [[ ! -f "$WG_CONF" ]]; then
  SERVER_PRIVATE_KEY=$(wg genkey)
  SERVER_PUBLIC_KEY=$(echo "$SERVER_PRIVATE_KEY" | wg pubkey)
  cat <<WGCONF > "$WG_CONF"
[Interface]
Address = $VPN_ADDRESS
ListenPort = $LISTEN_PORT
PrivateKey = $SERVER_PRIVATE_KEY
SaveConfig = true
PostUp = iptables -A FORWARD -i $WG_INTERFACE -j ACCEPT; iptables -A FORWARD -o $WG_INTERFACE -j ACCEPT; iptables -t nat -A POSTROUTING -o $(ip route get 1.1.1.1 | awk '{print $5; exit}') -j MASQUERADE
PostDown = iptables -D FORWARD -i $WG_INTERFACE -j ACCEPT; iptables -D FORWARD -o $WG_INTERFACE -j ACCEPT; iptables -t nat -D POSTROUTING -o $(ip route get 1.1.1.1 | awk '{print $5; exit}') -j MASQUERADE
WGCONF
  chmod 600 "$WG_CONF"
else
  SERVER_PUBLIC_KEY=$(wg show $WG_INTERFACE public-key || true)
fi

systemctl enable wg-quick@$WG_INTERFACE
systemctl restart wg-quick@$WG_INTERFACE || true

rm -rf "$INSTALL_DIR"
mkdir -p "$BACKEND_DIR" "$FRONTEND_DIR" "$INSTALL_DIR/config"
rsync -a "$REPO_DIR/backend/" "$BACKEND_DIR/"
rsync -a "$REPO_DIR/frontend/" "$FRONTEND_DIR/"
rsync -a "$REPO_DIR/config/" "$INSTALL_DIR/config/"
cp "$REPO_DIR/.env.example" "$INSTALL_DIR/.env.example"
cp "$REPO_DIR/README.md" "$INSTALL_DIR/README.md"

python3 -m venv "$BACKEND_DIR/venv"
source "$BACKEND_DIR/venv/bin/activate"
pip install --upgrade pip
pip install -r "$BACKEND_DIR/requirements.txt"
deactivate

pushd "$FRONTEND_DIR" >/dev/null
npm install
npm run build
popd >/dev/null

mkdir -p /var/www/myvpn
cp -r "$FRONTEND_DIR/dist"/* /var/www/myvpn/

TEMP_ADMIN_PASS=$(openssl rand -hex 8)
JWT_SECRET=$(openssl rand -hex 32)
PUBLIC_ENDPOINT=$(curl -s https://ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}'):$LISTEN_PORT
cat <<ENV > "$ENV_FILE"
ADMIN_USERNAME=admin
ADMIN_PASSWORD=$TEMP_ADMIN_PASS
JWT_SECRET_KEY=$JWT_SECRET
DATABASE_URL=sqlite:///$INSTALL_DIR/backend/vpn.db
WG_INTERFACE=$WG_INTERFACE
WG_CONF_PATH=$WG_CONF
VPN_NETWORK_CIDR=$VPN_NETWORK
VPN_DNS=1.1.1.1, 8.8.8.8
SERVER_PUBLIC_ENDPOINT=$PUBLIC_ENDPOINT
FRONTEND_BASE_URL=https://myvpn.domain
ENV

cat <<SERVICE >/etc/systemd/system/vpn-dashboard.service
[Unit]
Description=WireGuard VPN Dashboard API
After=network.target

[Service]
WorkingDirectory=$BACKEND_DIR
EnvironmentFile=$ENV_FILE
ExecStart=$BACKEND_DIR/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=on-failure
KillSignal=SIGINT

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable --now vpn-dashboard.service

cp "$INSTALL_DIR/config/nginx.conf" /etc/nginx/sites-available/vpn-dashboard.conf
ln -sf /etc/nginx/sites-available/vpn-dashboard.conf /etc/nginx/sites-enabled/vpn-dashboard.conf
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

cat <<MSG
Installation complete! Access the dashboard at: https://myvpn.domain
Temporary admin credentials:
  Username: admin
  Password: $TEMP_ADMIN_PASS

Remember to update your DNS for myvpn.domain and issue TLS certificates (e.g., via certbot).
MSG
