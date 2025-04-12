from flask import Flask, request, render_template_string, redirect, url_for, session, Response
import os, subprocess, shutil, sys, json

if os.geteuid() != 0:
    print("This script needs to be run as root or sudo, try 'sudo python3 wg_helper.py'")
    sys.exit(1)


# ===================== #
ADMIN_PASSWORD = ""
# ===================== #


app = Flask(__name__)
app.secret_key = os.urandom(24)
wireguard_dir = "/etc/wireguard"
config_file = "wg_helper.json"
full_config_file_path = os.path.join(wireguard_dir, config_file)
SYSCTL_CONF = "/etc/sysctl.conf"


default_config = {
    "server": {
        "server_network_interface": subprocess.run("ip -o -4 route show to default | awk '{print $5}'", shell=True, capture_output=True, text=True).stdout.strip(),
        "Endpoint": "",
        "ListenPort": 51820,
        "PrivateKey": "",
        "PublicKey": ""
    },
    "peers": [
    ]
}


@app.route("/", methods=["GET", "POST"])
def login():
    LOGIN_HTML = """
        <!doctype html>
        <body style='font-family:sans-serif'>
        <title>WireGuard Helper - Login</title>
        <h2>Login</h2>
        <form method="POST">
            <input type="password" name="password" placeholder="Enter password">
            <input type="submit" value="Login">
            {% if error %}<p style="color:red;">{{ error }}</p>{% endif %}
        </form>
        </html>
        """
        
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        else:
            return render_template_string(LOGIN_HTML, error="Incorrect password, try again")
    return render_template_string(LOGIN_HTML, error=None)



@app.route("/dashboard")
def dashboard():
    ensure_logged_in()
    config_data = load_config()

    # One liners
    is_wg_installed = shutil.which("wg") is not None
    is_ufw_installed = ufw_get_path()
    server_network_interface = config_data.get("server", {}).get("server_network_interface", "")


    install_wg_button = ""
    if not is_wg_installed:
        install_wg_button = """ - 
        <form action="/install_wireguard" method="POST" style='display:inline'>
            <input type="submit" value="Install WireGuard">
        </form>
        """

    ufw_allow_port_button = """
    <form action='/ufw_open_port' method='POST' style='display:inline'> <input type='submit' value='Open Port 51820'></form>
    """

    wg_installed_status = "Installed" if is_wg_installed else "Not installed"
    ufw_installed_status = "Installed" if is_ufw_installed else "Not installed"
    if ufw_installed_status == "Installed":
        ufw_path = ufw_get_path()
        ufw_enabled_status = subprocess.run(f"{ufw_path} status | awk '/Status:/ {{print $2}}'", shell=True, capture_output=True, text=True).stdout.strip()
        if ufw_enabled_status == "active":
            ufw_enabled_status = " & active <br>"
        else:
            ufw_enabled_status = " & disabled <br>"


    wg_running_status = ""
    if wg_installed_status == "Installed":
        wg_running_check = subprocess.run("systemctl is-active wg-quick@wg0", shell=True, capture_output=True, text=True).stdout.strip()
        if wg_running_check == "failed":
            wg_running_status = f"<strong>Wireguard status:</strong> Not running <form action='/start_wg' method='POST' style='display:inline'> <input type='submit' value='Start wireguard'></form><br>"
        else:
            wg_running_status = f"<strong>Wireguard status:</strong> Running <br>"



    wg_enabled_at_boot = ""
    wg_enabled_at_boot_check = subprocess.run(f"systemctl is-enabled wg-quick@wg0", shell=True, capture_output=True, text=True).stdout.strip()
    if wg_enabled_at_boot_check == "enabled":
        wg_enabled_at_boot = "<strong>Wireguard autostart at boot:</strong> Enabled<br>"
    else:
        wg_enabled_at_boot = "<strong>Wireguard autostart at boot:</strong> DISABLED <form action='/autostart_wg_on_boot' method='POST' style='display:inline'> <input type='submit' value='Autostart Wireguard at boot'></form><br>"
    



    ufw_port_status = ""
    if ufw_enabled_status == " & active":
        ufw_wg_port_check = subprocess.run(f"{ufw_path} status | awk '/51820/ {{print $2; exit}}'", shell=True, capture_output=True, text=True).stdout.strip()
        if ufw_wg_port_check == "":
            ufw_port_status = f"<br><strong>UFW Wireguard Port:</strong> Not added - {ufw_allow_port_button}<br>"
        else:
            ufw_port_status = f"<br><strong>UFW Wireguard Port: </strong>{'Allowed' if ufw_wg_port_check == 'ALLOW' else f'Denied{ufw_allow_port_button}'}<br>"


    # Endpoint data
    server_endpoint_data = config_data.get("server", {}).get("Endpoint", "")
    if server_endpoint_data == "":
        server_endpoint_form = """
        <form action="/update_server_endpoint" method="POST" style='display:inline'>
            <input type="text" placeholder="Set server endpoint" name='endpoint'>
            <input type="submit" value="Set endpoint">
        </form>
        """
    else:
        server_endpoint_form = f""" {server_endpoint_data} 
        <form action="/update_server_endpoint" method="POST" style='display:inline'>
            <input type="text" placeholder='Enter new endpoint' name='endpoint'>
            <input type="submit" value="Update endpoint">
        </form>
        """


    # Server public key
    server_public_key = config_data.get("server", {}).get("PublicKey", "")
    if server_public_key == "":
        server_public_key_form = f""" No Keys set 
        <form action="/regenerate_server_keys" method="POST" style='display:inline'>
            <input type="submit" value="Generate server keys">
        </form>
        """
    else:
        server_public_key_form = f""" {server_public_key} 
        <form action="/regenerate_server_keys" method="POST" style='display:inline'>
            <input type="submit" value="Regenerate server keys">
        </form>
        """


    # Peers list
    peers_list = ""
    peer_config = config_data.get("peers", [])
    for peer in peer_config:
        peer_id = peer["id"]
        peer_name = peer["name"]
        peer_public_key = peer["PublicKey"]

        peers_list += f"""
        <strong>ID:</strong> {peer_id} - 
        <strong>Name:</strong> {peer_name} - 
        <strong>PublicKey:</strong> {peer_public_key}  
        <form action='/delete_peer' method='POST' style='display:inline'>
            <input type='hidden' name='peer_id_to_delete' value='{peer_id}'>
            <input type='submit' value='Delete peer'>
        </form> 
        <form action='/download_peer_config' method='POST' style='display:inline'>
            <input type='hidden' name='peer_id' value='{peer_id}'>
            <input type='submit' value='Download config file'>
        </form> 
        <br>"""



    html = f"""
    <!doctype html>
    <body style='font-family:sans-serif'>
    <title>SeaBee's WG Helper</title>
    <h1>SeaBee's Wireguard Helper v0.1</h1>
    <a href="/logout">Logout</a>
    <hr>

    <h2>System status</h2>
    <strong>Wireguard software:</strong> {wg_installed_status}{install_wg_button}<br>
    {wg_running_status}
    {wg_enabled_at_boot}
    <strong>UFW:</strong> {ufw_installed_status}{ufw_enabled_status}
    {ufw_port_status}
    <strong>Server network interface:</strong> {server_network_interface}
    <hr>

    <h2>Options</h2>
    <strong>Server endpoint:</strong> {server_endpoint_form} <br><br>
    <strong>Server Public key:</strong> {server_public_key_form} <br><br>


    <hr>

    <h2>Peers</h2>
    <strong>Create new peer: </strong> 
    <form action="/create_new_peer" method="POST" style='display:inline'>
        <input type="text" placeholder="Peer name" name="peer_name">
        <input type="submit" value="Create">
    </form><br><br>
    {peers_list}


    </body>
    """
    return html




@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


def ensure_logged_in():
    if not session.get("logged_in"):
        return redirect(url_for("login"))


@app.route("/install_wireguard", methods=["POST"])
def install_wireguard():
    ensure_logged_in()

    try:
        subprocess.check_call(["sudo", "apt", "install", "-y", "wireguard"])
    except subprocess.CalledProcessError as e:
        return f"<p>Installation failed: {e}</p><a href='/dashboard'>Back</a>"

    return redirect(url_for("dashboard"))


@app.route("/update_server_endpoint", methods=["POST"])
def update_server_endpoint():
    
    new_endpoint = request.form.get("endpoint", "").strip()

    config_data = load_config()
    config_data.setdefault("server", {})["Endpoint"] = new_endpoint

    update_config(config_data)

    return redirect(url_for("dashboard"))


@app.route("/ufw_open_port", methods=["POST"])
def ufw_open_port():
    ensure_logged_in()

    ufw_path = ufw_get_path()

    try:
        subprocess.check_call([ufw_path, "allow", "51820", "comment", '"Wireguard"'])
    except subprocess.CalledProcessError as e:
        return f"<p>Installation failed: {e}</p><a href='/dashboard'>Back</a>"

    return redirect(url_for("dashboard"))


@app.route("/regenerate_server_keys", methods=["POST"])
def regenerate_server_keys():

    private_key = subprocess.check_output(["wg", "genkey"], text=True).strip()
    public_key = subprocess.check_output(["wg", "pubkey"], input=private_key, text=True).strip()

    config_data = load_config()

    config_data.setdefault("server", {})["PrivateKey"] = private_key
    config_data.setdefault("server", {})["PublicKey"] = public_key

    update_config(config_data)

    return redirect(url_for("dashboard"))


@app.route("/create_new_peer", methods=["POST"])
def create_new_peer():
    new_peer_name = request.form.get("peer_name", "").strip()

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
        "name": new_peer_name,
        "PrivateKey": private_key,
        "PublicKey": public_key
    }

    peers.append(new_peer)
    peers = sorted(peers, key=lambda peer: peer.get("id", 0))

    config_data["peers"] = peers

    update_config(config_data)

    return redirect(url_for("dashboard"))


@app.route("/delete_peer", methods=["POST"])
def delete_peer():
    peer_id_to_delete = request.form.get("peer_id_to_delete", "").strip()
    peer_id_to_delete = int(peer_id_to_delete)
    config_data = load_config()
    peer_config = config_data.get("peers", [])

    # Literally just set the peers to itself minus the peer ID requested
    new_peer_config = [peer for peer in peer_config if peer["id"] != peer_id_to_delete]
    new_peer_config = sorted(new_peer_config, key=lambda peer: peer.get("id", 0))

    config_data["peers"] = new_peer_config

    update_config(config_data)

    return redirect(url_for("dashboard"))


@app.route("/download_peer_config", methods=["POST"])
def download_peer_config():
    peer_id_to_download = request.form.get("peer_id", "").strip()
    peer_id_to_download = int(peer_id_to_download)

    config_data = load_config()
    peer_config = config_data.get("peers", [])

    selected_peer = None
    for peer in peer_config:
        if peer.get("id") == peer_id_to_download:
            selected_peer = peer
            break

    if not selected_peer:
        return "Peer not found", 404

    peer_name = selected_peer["name"]
    peer_pub_key = selected_peer["PublicKey"]
    peer_priv_key = selected_peer["PrivateKey"]

    server_pub_key = config_data["server"]["PublicKey"]
    endpoint = config_data["server"]["Endpoint"]
    listen_port = config_data["server"]["ListenPort"]
    interface = config_data["server"]["server_network_interface"]

    # Compose the WireGuard peer config
    config_text = f"""[Interface]
    PrivateKey = {peer_priv_key}
    Address = 10.0.0.{peer_id_to_download}/24
    DNS = 1.1.1.1

[Peer]
    PublicKey = {server_pub_key}
    Endpoint = {endpoint}:{listen_port}
    AllowedIPs = 0.0.0.0/0
    PersistentKeepalive = 25
    """

    # Create response with downloadable config file
    filename = f"peer_{peer_name}.conf"
    return Response(
        config_text,
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.route("/start_wg", methods=["POST"])
def start_wg():
    subprocess.run(["wg-quick", "up", "wg0"], text=True)

    return redirect(url_for("dashboard"))


@app.route("/autostart_wg_on_boot", methods=["POST"])
def enable_wg_at_boot():
    subprocess.run(["systemctl", "enable", "wg-quick@wg0"], text=True)

    return redirect(url_for("dashboard"))




def ufw_get_path():
    ensure_logged_in()

    ufw_dirs = ["/bin", "/sbin", "/usr/bin", "/usr/sbin", "/usr/local/bin", "/usr/local/sbin"]

    for dir in ufw_dirs:
        path = os.path.join(dir, "ufw")
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    
    return None


def run_first_install_setup():
    # Create /etc/wireguard folder
    if not os.path.exists(wireguard_dir):
        os.mkdir(wireguard_dir)
    
    # Create config json
    if not os.path.isfile(full_config_file_path):
        with open(full_config_file_path, "w") as f:
            json.dump(default_config, f, indent=4)

    # Create wg0.conf
    if not os.path.isfile("/etc/wireguard/wg0.conf"):
        update_config(load_config())

    # Port forward
    update_sysctl()


def update_sysctl():
    try:
        with open(SYSCTL_CONF, "r") as file:
            lines = file.readlines()

        modified = False
        found = False

        for i in range(len(lines)):
            if "net.ipv4.ip_forward=" in lines[i]:  
                found = True
                if lines[i].strip().startswith("#"):  # If commented, uncomment
                    lines[i] = lines[i].lstrip("#")  # Remove leading #
                    modified = True
                if lines[i].strip() != "net.ipv4.ip_forward=1":  # Ensure it's set to 1
                    lines[i] = "net.ipv4.ip_forward=1\n"
                    modified = True

        if not found:  # If not found, append it
            lines.append("\nnet.ipv4.ip_forward=1\n")
            modified = True

        if modified:
            with open(SYSCTL_CONF, "w") as file:
                file.writelines(lines)
            os.system("sudo sysctl -p")  # Apply changes
            print("Updated sysctl.conf and applied changes.")
        else:
            print("No changes needed.")

    except Exception as e:
        print(f"Error: {e}")


def load_config():
    try:
        with open(full_config_file_path, "r") as f:
            return json.load(f)
    except:
        return(0)


def update_config(config_data):
    with open(full_config_file_path, "w") as f:
        json.dump(config_data, f, indent=4)

    peers = config_data.get("peers", [])
    server_priv_key = config_data.get("server", {}).get("PrivateKey", "")
    server_pub_key = config_data.get("server", {}).get("PublicKey", "")
    server_endpoint = config_data.get("server", {}).get("Endpoint", "")
    server_network_interface = config_data.get("server", {}).get("server_network_interface", "")


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

        wg_config_content += f"""
[Peer]
        PublicKey = {peer_pub_key}
        AllowedIPs = 10.0.0.{peer_id}/24
        """

    subprocess.run(["systemctl", "stop", "wg-quick@wg0"], text=True)
    with open("/etc/wireguard/wg0.conf", "w") as f:
        f.write(wg_config_content)

    print("Server config updated")
    print("restarting wireguard service")
    subprocess.run(["systemctl", "start", "wg-quick@wg0"], text=True)



if __name__ == "__main__":
    run_first_install_setup()
    app.run(host="0.0.0.0", port=5050)



