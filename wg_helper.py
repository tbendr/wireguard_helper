# Wireguard helper v0.1

import os, subprocess, sys, json
print("Welcome to SeaBee's Wireguard helper")


config_dir = "/etc/wireguard"
config_file = "wg_helper.json"


# Default configuration
default_config = {
    "server_variables": {
        "ufw": None,
        "network_interface":""
    },
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
        print("2: View & edit peers")
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

                if not os.path.exists(f"{config_dir}/{config_file}"):
                    print(f"Config file {config_file} not found. Creating now...")
                    create_config_file(config_file)

                config_data = load_config()
                server_vars = config_data.get("server_vars", {})

                server_network_interface = subprocess.run("ip -o -4 route show to default | awk '{print $5}'", shell=True, capture_output=True, text=True).stdout.strip()

                server_vars["network_interface"] = server_network_interface
                config_data["server_vars"] = server_vars

                with open(f"{config_dir}/{config_file}", "w") as f:
                    json.dump(config_data, f, indent=4)



            else:
                print("wireguard already installed")
            

            print("Checking if wg0.conf exists\n")
            setup_wg0conf()

            continue

        
        elif choice == "2":
            print("\nPeer info")

            config_data = load_config()
            peer_config = config_data.get("peers", [])

            print("Peers")
            for peer in peer_config:
                peer_id = peer["id"]
                peer_name = peer["name"]
                peer_public_key = peer["PublicKey"]

                print(f"ID: {peer_id} - Name: {peer_name} - PublicKey: {peer_public_key}")
            
            if input("\nWould you like to delete any peers? (y/n): ") == "y":
                peer_choice = input("Type peer ID to delete, type 'q' to go back to main menu: ")
                if peer_choice == "q":
                    continue

                try:
                    peer_id_to_delete = int(peer_choice)
                except ValueError:
                    print("Invalid ID. Please enter a numeric ID.")
                    continue

                # Filter out the peer with the matching ID
                new_peer_config = [peer for peer in peer_config if peer["id"] != peer_id_to_delete]

                if len(new_peer_config) == len(peer_config):
                    print(f"No peer found with ID {peer_id_to_delete}.")
                else:
                    config_data["peers"] = new_peer_config

                    # Save the updated peer list back to the config file
                    with open(f"{config_dir}/{config_file}", "w") as f:
                        json.dump(config_data, f, indent=4)
                    
                    print(f"\nPeer with ID {peer_id_to_delete} has been deleted.")

                    write_json_to_config_file()

            continue

        elif choice == "3":
            config_data = load_config()
            peers = config_data.get("peers", [])

            existing_ids = sorted(peer["id"] for peer in peers)

            # Find available ID by checking gaps
            existing_ids = sorted(peer["id"] for peer in peers)  # Get all assigned IDs, sorted

            # Start from 2, find the first missing number
            new_id = 2
            for id in existing_ids:
                if id == new_id:
                    new_id += 1
                else:
                    break  # Found a gap, use it

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
            with open(f"{config_dir}/{config_file}", "w") as f:
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
        else:
            print("Unsupported package manager. Install manually.")
            return

        print(f"wireguard installed successfully!")
    
    except subprocess.CalledProcessError as e:
        print(f"Failed to install wireguard: {e}")


def create_config_file(config_file):
    try:
        with open(f"{config_dir}/{config_file}", "w") as f:
            json.dump(default_config, f, indent=4)
            print(f"Config file {config_file} created successfully.")
    except IOError as e:
        print(f"Failed to create config file: {e}")


def load_config():
    if(not os.path.exists(f"{config_dir}/{config_file}")):
        create_config_file(f"{config_dir}/{config_file}")
    try:
        with open(f"{config_dir}/{config_file}", "r") as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Failed to load config file: {e}")


def write_json_to_config_file():
    config_data = load_config()
    peers = config_data.get("peers", [])

    server_priv_key = config_data.get("server", {}).get("PrivateKey", "")
    server_pub_key = config_data.get("server", {}).get("PublicKey", "")
    server_endpoint = config_data.get("server", {}).get("Endpoint", "")
    server_network_interface = config_data.get("server_vars", {}).get("network_interface", "")


    wg_config_content = f"""[Interface]
        Address = 10.0.0.1/24
        SaveConfig = true
        PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -t nat -A POSTROUTING -o {server_network_interface} -j MASQUERADE
        PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -t nat -D POSTROUTING -o {server_network_interface} -j MASQUERADE
        ListenPort = 51820
        PrivateKey = {server_priv_key}
        """

    for peer in peers:
        peer_id = peer["id"]
        peer_name = peer["name"]
        peer_pub_key = peer["PublicKey"]
        peer_priv_key = peer["PrivateKey"]

        wg_config_content += f"""[Peer]
        PublicKey = {peer_pub_key}
        AllowedIPs = 10.0.0.{peer_id}/24
        """

        with open(f"{config_dir}/peer{peer_id}-{peer_name}.conf", "w") as f:
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


    with open(f"{config_dir}/wg0.conf", "w") as f:
        f.write(wg_config_content)

    print("Server config updated")



def setup_wg0conf():
    config_data = load_config()
    server_config = config_data.get("server", {})

    server_software = config_data.get("server_software", {})
    ufw_is_installed = server_software.get("ufw", "")

    if ufw_is_installed == None:
        ufw_output = subprocess.run(["dpkg", "-l"], text=True, stdout=subprocess.PIPE).stdout
        if "ufw" in ufw_output:
            server_software["ufw"] = True
            subprocess.run(["ufw","allow", "51820"])
        else:
            server_software["ufw"] = False


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
    config_data["server_software"] = server_software

    with open(f"{config_dir}/{config_file}", "w") as f:
        json.dump(config_data, f, indent=4)

    write_json_to_config_file()
    
    print("wg0.conf generated for server")


def restart_wg():
    subprocess.run(["sudo", "systemctl", "restart", "wg-quick@wg0"], text=True).strip()


def start_wg():
    subprocess.run(["wg-quick", "up", "wg0"], text=True).strip()



if __name__ == "__main__":
    main()
