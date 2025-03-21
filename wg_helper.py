# Wireguard helper v0.1

import os, subprocess, sys, json
print("Welcome to SeaBee's Wireguard helper")


def main():
    while True:
        config_dir = "/etc/wireguard"
        config_file = "/etc/wireguard/wg_helper.json"



        print("\nPlease type a number for what you would like to do")
        print("1: Install wireguard")
        print("2: Create server config")
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
                print("wireguard already installed, going back to menu")
        
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










if __name__ == "__main__":
    main()
