# Self-Hosted WireGuard VPN Dashboard

> **For personal, legal, private use only.**

Modern FastAPI + React stack to manage a WireGuard server, issue client configs, and share them as QR codes. The project ships with an automated installer for Ubuntu, nginx reverse-proxy config, and a dark dashboard UI.

## Project layout
```
backend/   FastAPI + SQLite API (uvicorn entrypoint `app.main:app`)
frontend/  React + Vite dashboard (dark UI)
scripts/install_vpn.sh  Automated Ubuntu installer
config/nginx.conf       Reverse proxy template (. -> frontend build, /api -> backend)
.env.example            Environment variable template
README.md               This file
```

## Requirements
- Ubuntu 22.04+ server with sudo/root access
- Public DNS record pointing to your host (e.g. `myvpn.domain`)
- Ports 80 (HTTP), 443 (HTTPS), and 51820/UDP reachable

## Quick install
Run the installer from the repository root on a fresh Ubuntu server:

```bash
sudo chmod +x scripts/install_vpn.sh
sudo scripts/install_vpn.sh
```

The script will:
1. Install WireGuard, Python, Node.js, nginx, and dependencies.
2. Enable IPv4/IPv6 forwarding and set up `/etc/wireguard/wg0.conf`.
3. Deploy the FastAPI backend as a systemd service (`vpn-dashboard.service`).
4. Build the React frontend into `/var/www/myvpn`.
5. Install the nginx reverse proxy (HTTP by default – add TLS via certbot).
6. Print the dashboard URL plus a temporary admin password.

> After running certbot or adding your own certificates, update `/etc/nginx/sites-available/vpn-dashboard.conf` to listen on 443 with SSL.

## Accessing the dashboard
1. Visit `https://myvpn.domain` (replace with your DNS).
2. Log in using the temporary credentials printed by the installer.
3. Immediately change `ADMIN_PASSWORD` inside `/opt/vpn-dashboard/.env` and restart the backend: `sudo systemctl restart vpn-dashboard.service`.

## Managing VPN clients
- **Add client**: Click “Add Client”, provide a friendly device name, and the API will generate keys, assign an IP, update `wg0.conf`, and push the peer to the kernel using `wg addconf`.
- **Download config**: Use the “Config” button to download the `.conf` file. Import it into WireGuard Desktop (Windows/macOS/Linux).
- **Show QR**: Use the “QR” button to display a base64 PNG QR code for quick import on WireGuard iOS/Android apps.
- **Remove client**: Hit “Delete” to remove the peer from both SQLite and the running interface via `wg set <iface> peer <key> remove`.

## Using the WireGuard profiles
- **iPhone / Android**: Install the official WireGuard app, tap “Add Tunnel → Create from QR code”, and scan the QR shown in the dashboard.
- **Windows / macOS / Linux Desktop**: Download the `.conf` file and import it into the WireGuard application. Alternatively, copy the text into a new tunnel.
- **CLI (Linux)**: Save the config as `/etc/wireguard/mydevice.conf`, then run `sudo wg-quick up mydevice`.

## Backend environment variables
All tunables live in `.env` (see `.env.example`):

| Variable | Description |
| --- | --- |
| `ADMIN_USERNAME`, `ADMIN_PASSWORD` | Dashboard login credentials |
| `JWT_SECRET_KEY` | Secret used to sign API tokens |
| `DATABASE_URL` | SQLite location (default `sqlite:///./vpn.db`) |
| `WG_INTERFACE` / `WG_CONF_PATH` | WireGuard interface + config path |
| `VPN_NETWORK_CIDR` | Address pool for clients (e.g. `10.8.0.0/24`) |
| `VPN_DNS` | DNS servers pushed to clients |
| `SERVER_PUBLIC_ENDPOINT` | Public endpoint `<host>:<port>` clients use |
| `FRONTEND_BASE_URL` | Used by CORS middleware |

Reload the backend service any time you edit `.env`:
```bash
sudo systemctl restart vpn-dashboard.service
```

## Development
- Backend: `cd backend && uvicorn app.main:app --reload`
- Frontend: `cd frontend && npm install && npm run dev`
- WireGuard commands in development are the real ones (`wg`, `wg-quick`). Use caution and run against a test host.

## Legal
This project is intended for lawful personal use. Ensure VPN usage complies with your jurisdiction and service-provider policies.
