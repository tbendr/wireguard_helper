# SeaBee's WireGuard Helper Script

This Python script simplifies the installation and management of a WireGuard VPN server, including client configuration.

## 🔧 Features

- Installs WireGuard and required dependencies
- Generates server and peer key pairs
- Edits and manages the WireGuard config file (`wg0.conf`)
- Stores configuration data in a JSON file for easy reuse
- Allows editing the server endpoint
- Starts a temporary web admin panel for WireGuard management
- Automatically opens port `51820` using UFW (if enabled)

## 📦 Requirements

- Python 3
- Flask (`sudo apt install python3-flask` **or** `pip install flask`)
- A Linux-based system
- Internet connection

> ⚠️ Note: This script has been tested on debain and may not work on your machine

## 🚀 Installation & Usage

1. **Download** the script to any directory on your system.

```bash
curl -L -o wg_helper.py https://raw.githubusercontent.com/seabee33/wireguard_helper/main/wg_helper.py
```
4. **Set the admin password** on **line 10** of the file: `ADMIN_PASSWORD = "your_secure_password_here"`
    
5. **Run the script with sudo or as root** `sudo python3 wg_helper.py`

6. Access the web panel: Open your browser and go to: `http://<SERVER_IP>:5050`

