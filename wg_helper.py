from flask import Flask, request, render_template_string, redirect, url_for, session
import os, subprocess, shutil, sys

if os.geteuid() != 0:
    print("This script needs to be run as root or sudo, try 'sudo python3 wg_helper.py'")
    sys.exit(1)

app = Flask(__name__)
app.secret_key = os.urandom(24)


# ===================== #
ADMIN_PASSWORD = ""
# ===================== #



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
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    
    is_wg_installed = shutil.which("wg") is not None
    is_ufw_installed = ufw_get_path()

    install_wg_button = ""
    if not is_wg_installed:
        install_wg_button = """ - 
        <form action="/install-wireguard" method="POST" style='display:inline'>
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
            ufw_enabled_status = " & active"
        else:
            ufw_enabled_status = " & disabled"
    # server_network_interface = subprocess.run("ip -o -4 route show to default | awk '{print $5}'", shell=True, capture_output=True, text=True).stdout.strip()

    ufw_port_status = ""
    if ufw_enabled_status == " & active":
        ufw_wg_port_check = subprocess.run(f"{ufw_path} status | awk '/51820/ {{print $2; exit}}'", shell=True, capture_output=True, text=True).stdout.strip()
        if ufw_wg_port_check == "":
            ufw_port_status = f"<br><strong>UFW Wireguard Port:</strong> Not added - {ufw_allow_port_button}<br>"
        else:
            ufw_port_status = f"<br><strong>UFW Wireguard Port: </strong>{'Allowed' if ufw_wg_port_check == 'ALLOW' else f'Denied{ufw_allow_port_button}'}"



    html = f"""
    <!doctype html>
    <body style='font-family:sans-serif'>
    <title>WG Helper</title>
    <h1>Wireguard Helper v0.1</h1>
    <a href="/logout">Logout</a>
    <hr>

    <h2>System status</h2>
    <strong>Wireguard:</strong> {wg_installed_status}{install_wg_button}<br>
    <strong>UFW:</strong> {ufw_installed_status}{ufw_enabled_status}
    {ufw_port_status}


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


@app.route("/install-wireguard", methods=["POST"])
def install_wireguard():
    ensure_logged_in()

    try:
        subprocess.check_call(["sudo", "apt", "install", "-y", "wireguard"])
    except subprocess.CalledProcessError as e:
        return f"<p>Installation failed: {e}</p><a href='/dashboard'>Back</a>"

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


def ufw_get_path():
    ensure_logged_in()

    ufw_dirs = ["/bin", "/sbin", "/usr/bin", "/usr/sbin", "/usr/local/bin", "/usr/local/sbin"]

    for dir in ufw_dirs:
        path = os.path.join(dir, "ufw")
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    
    return None



























if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)



