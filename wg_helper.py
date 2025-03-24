# Wireguard helper v0.1

import os, subprocess, sys, json
print("Welcome to SeaBee's Wireguard helper")



# config_dir = "/etc/wireguard"
# config_file = "/etc/wireguard/wg_helper.json"

config_dir = ""
config_file = "wg_helper.json"

# Default configuration
default_config = {
    "server": {
        "Endpoint": "",
        "ListenPort": 51820,
        "PrivateKey": "",
        "PublicKey": ""
    },
    "peers": [
    ]
}

def main():
    while True:

        print("\nPlease type a number for what you would like to do")
        print("1: Install & initilize wireguard")
        print("2: View peers")
        print("3: Add new peer")

        print("q: Exit the script")

        choice = input("").strip()
        print("\n")


        if choice == "1":
            print("Checking if wireguard is already installed")
            if check_if_wireguard_already_installed() == False:
                print("wireguard package not found, installing now")
                install_wireguard()

                if not os.path.exists(config_dir):
                    print(f"Directory {config_dir} not found. Creating now...")
                    os.makedirs(config_dir, exist_ok=True)

                if not os.path.exists(config_file):
                    print(f"Config file {config_file} not found. Creating now...")
                    create_config_file(config_file)

            else:
                print("wireguard already installed")
            

            print("Checking if wg0.conf exists\n")
            setup_wg0conf()

            continue

        
        elif choice == "2":
            print("\nServer Config")

            config_data = load_config(config_file)
            server_config = config_data.get("server", {})

            print(f"Endpoint: {server_config.get('Endpoint', '-')}")
            continue

        elif choice == "3":
            config_data = load_config(config_file)
            peers = config_data.get("peers", [])

            # Get current IDs and add 1
            if peers:
                max_id = max(client["id"] for client in peers)
            else:
                max_id = 1
            new_id = max_id + 1

            # Generate new keys
            private_key = subprocess.check_output(["wg", "genkey"], text=True).strip()
            public_key = subprocess.check_output(["wg", "pubkey"], input=private_key, text=True).strip()

            # Create new peer info
            new_peer = {
                "id": new_id,
                "name": input("Peer name: "),
                "PrivateKey": private_key,
                "PublicKey": public_key
            }

            peers.append(new_peer)
            config_data["peers"] = peers

            # Save new peer
            with open(config_file, "w") as f:
                json.dump(config_data, f, indent=4)
            
            print("New peer added")
            print("Now updating config file")
            write_json_to_config_file()

        elif choice == "q":
            print("Exiting")
            break

        else:
            print("Invalid choice")

        print("\n")


def check_if_wireguard_already_installed():
    try:
        # Check for the package with different package managers
        if subprocess.run(["which", "wireguard"], stdout=subprocess.DEVNULL).returncode == 0:
            return True  # Package found in the system PATH
        elif subprocess.run(["dpkg", "-l", "wireguard"], stdout=subprocess.DEVNULL).returncode == 0:  # For apt-based systems
            return True
        elif subprocess.run(["rpm", "-q", "wireguard"], stdout=subprocess.DEVNULL).returncode == 0:  # For RPM-based systems
            return True
        elif subprocess.run(["pacman", "-Q", "wireguard"], stdout=subprocess.DEVNULL).returncode == 0:  # For Arch-based systems
            return True
        else:
            return False  # Package not found
    except subprocess.CalledProcessError:
        return False


def install_wireguard():
    try:
        # Detect package manager
        if subprocess.run(["which", "apt"], stdout=subprocess.DEVNULL).returncode == 0:
            subprocess.run(["sudo", "apt", "update", "-y"], check=True)
            subprocess.run(["sudo", "apt", "install", "-y", "wireguard"], check=True)
        elif subprocess.run(["which", "dnf"], stdout=subprocess.DEVNULL).returncode == 0:
            subprocess.run(["sudo", "dnf", "install", "-y", "wireguard"], check=True)
        elif subprocess.run(["which", "pacman"], stdout=subprocess.DEVNULL).returncode == 0:
            subprocess.run(["sudo", "pacman", "-Sy", "--noconfirm", "wireguard"], check=True)
        elif subprocess.run(["which", "zypper"], stdout=subprocess.DEVNULL).returncode == 0:
            subprocess.run(["sudo", "zypper", "install", "-y", "wireguard"], check=True)
        else:
            print("Unsupported package manager. Install manually.")
            return

        print(f"wireguard installed successfully!")
    
    except subprocess.CalledProcessError as e:
        print(f"Failed to install wireguard: {e}")


def create_config_file(config_file):
    try:
        with open(config_file, "w") as f:
            json.dump(default_config, f, indent=4)
            print(f"Config file {config_file} created successfully.")
    except IOError as e:
        print(f"Failed to create config file: {e}")


def load_config(config_file):
    if(not os.path.exists(config_file)):
        create_config_file(config_file)
    try:
        with open(config_file, "r") as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Failed to load config file: {e}")


def write_json_to_config_file():
    config_data = load_config(config_file)
    peers = config_data.get("peers", [])

    server_priv_key = config_data.get("server", {}).get("PrivateKey", "")
    server_pub_key = config_data.get("server", {}).get("PublicKey", "")
    server_endpoint = config_data.get("server", {}).get("Endpoint", "")


    wg_config_content = f"""[Interface]
Address = 10.0.0.1/24
SaveConfig = true
PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -t nat -A POSTROUTING -o enp10s0 -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -t nat -D POSTROUTING -o enp10s0 -j MASQUERADE
ListenPort = 51820
PrivateKey = {server_priv_key}
    """

    for peer in peers:
        peer_id = peer["id"]
        peer_pub_key = peer["PublicKey"]
        peer_priv_key = peer["PrivateKey"]

        wg_config_content += f"""
[Peer]
PublicKey = {peer_pub_key}
AllowedIPs = 10.0.0.{peer_id}/24
        """

        with open(f"peer{peer_id}.conf", "w") as f:
            f.write(f"""[Interface]
PrivateKey = {peer_priv_key}
Address = 10.0.0.{peer_id}
DNS = 1.1.1.1

[Peer]
PublicKey = {server_pub_key}
Endpoint = {server_endpoint}
AllowedIPs = 0.0.0.0/0
PersistentKeepAlive = 25
            """)


    with open("wg0.conf", "w") as f:
        f.write(wg_config_content)

    print("Server config updated")



def setup_wg0conf():
    config_data = load_config(config_file)
    server_config = config_data.get("server", {})

    server_priv_key = config_data.get("server", {}).get("PrivateKey", "")
    server_pub_key = config_data.get("server", {}).get("PublicKey", "")
    server_endpoint = config_data.get("server", {}).get("Endpoint", "")

    if server_endpoint == "":
        print("Server endpoint empty")
        new_server_endpoint = input("Enter server address or IP: ")
        server_config["Endpoint"] = new_server_endpoint
    else:
        update_endpoint = input("server endpoint already set\nType 'y' to update endpoint, type 'n' to not make any changes: ")
        if update_endpoint == "y":
            new_server_endpoint = input("Enter new server address or IP: ")
            server_config["Endpoint"] = new_server_endpoint
        else:
            print("Made no changes to endpoint")

    if server_priv_key == "":
        print("No server keys found\nGenerating new keys now")
        new_server_private_key = subprocess.check_output(["wg", "genkey"], text=True).strip()
        new_server_public_key = subprocess.check_output(["wg", "pubkey"], input=new_server_private_key, text=True).strip()

        server_config.update({
            "PrivateKey": new_server_private_key,
            "PublicKey": new_server_public_key
        })
    else:
        print("\nServer keys already set")
        update_server_keys = input("Type 'y' to refresh keys, type 'n' to not make any changes: ")
        if update_server_keys == "y":
            print("refreshing server keys now")
            new_server_private_key = subprocess.check_output(["wg", "genkey"], text=True).strip()
            new_server_public_key = subprocess.check_output(["wg", "pubkey"], input=new_server_private_key, text=True).strip()

            server_config.update({
                "PrivateKey": new_server_private_key,
                "PublicKey": new_server_public_key
            })
        else:
            print("Made no changes to server keys")
    
    config_data["server"] = server_config

    with open(config_file, "w") as f:
        json.dump(config_data, f, indent=4)

    write_json_to_config_file()
    
    print("wg0.conf generated for server")



if __name__ == "__main__":
    main()
