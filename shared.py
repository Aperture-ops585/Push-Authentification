import os
import json

# Directory configuration
PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(PROJECT_PATH, "credentials.json")
CONFIG_FILE = os.path.join(PROJECT_PATH, "config.json")

# Dynamic Configuration Loading
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

config_data = load_config()

# Domain/Identity parameters
RP_ID = config_data.get("rp_id", "web-auth.duckdns.org") #Relying Party ID for security
RP_NAME = config_data.get("rp_name", "My Workstation Auth") #Relying Party Name for security
ORIGIN = config_data.get("rp_origin", f"https://{RP_ID}") #Origin of the request

# Dynamic Challenge Cache (Shared across modules)
ACTIVE_CHALLENGES = {}

# Single-User Database Operations
def load_credential():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return None

def save_credential(cred_id, public_key, sign_count):
    with open(DB_FILE, "w") as f:
        json.dump({
            "id": cred_id,
            "public_key": public_key,
            "sign_count": sign_count
        }, f)
