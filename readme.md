# SeaBee's wireguard helper script

This is a python script to make the installation and management of wireguard server side easier

This script can:
- Install wireguard
- Generate server keys
- Generate peer keys
- Edit server endpoint
- Save all the data to a json config file

Requirements:
- Python3
- flask library for flask ("sudo apt install python3-flask" OR "pip install flask")
- A linux machine
- Internet


To install this script:

1 - Download the python file to anywhere

2 - Set the admin password on line 13 of the file (IMPORTANT)

3 - Run the file with python `python3 wg_helper.py`

4 - Go to your browser on your server or client machine and go to SERVER_IP:5050
