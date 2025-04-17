# WireGuard Helper (Containerized)

A containerized version of the WireGuard Helper application that simplifies the installation and management of a WireGuard VPN server.

## Prerequisites

- Docker
- Docker Compose
- Linux host system (recommended)

## Quick Start

1. Clone this repository:
```bash
git clone <repository-url>
cd wireguard_helper
```

2. Edit the `docker-compose.yml` file and set your desired admin password:
```yaml
environment:
  - ADMIN_PASSWORD=your_secure_password_here
```

3. Start the container:
```bash
docker-compose up -d
```

4. Access the web interface at: `http://<your-server-ip>:5050`

## Important Notes

- The container runs in privileged mode and uses host networking to ensure proper functionality of WireGuard and iptables
- WireGuard configuration files are persisted in `/etc/wireguard` on the host system
- The container exposes two ports:
  - 5050: Web interface
  - 51820/udp: WireGuard VPN port

## Security Considerations

- Always set a strong admin password in the docker-compose.yml file
- The container requires privileged access to manage network interfaces and iptables
- Consider using a reverse proxy with SSL/TLS for the web interface in production

## Troubleshooting

If you encounter issues:

1. Check container logs:
```bash
docker-compose logs
```

2. Verify WireGuard configuration:
```bash
docker exec wireguard-helper wg show
```

3. Check system logs:
```bash
docker exec wireguard-helper journalctl -u wg-quick@wg0
```

## License

[Your License Here]
