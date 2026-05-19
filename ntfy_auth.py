import requests
import json
import os

# Load configuration from JSON file — resolve relative to this module's location
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def send_auth_request(request_id, ip_address, service):
    """
    Sends a push notification using URLs and Tags from config.
    """
    config = load_config()
    topic_url = config.get("topic_url")
    response_url = config.get("response_url")
    token = config.get("ntfy_token")
    tags = config.get("tags")

    # Construct the biometric WebAuthn approval URL
    web_auth_domain = config.get("rp_id", "web-auth.duckdns.org")
    approval_url = f"https://{web_auth_domain}/approve?id={request_id}"

    deny_action = f"http, Use Password, {response_url}, method=POST, headers.Authorization=Bearer {token}, body=denied:{request_id}, clear=true"

    headers = {
        "Title": f"Auth Request: {service.upper()}",
        "Priority": "5",
        "Tags": tags,
        "Authorization": f"Bearer {token}",
        "Actions": (
            f"view, Approve (Biometric), {approval_url}, clear=true; "
            f"{deny_action}"
        )
    }

    message = f"{service.upper()} login attempt from {ip_address}. Do you approve?"
    
    response = requests.post(
        topic_url,
        data=message.encode('utf-8'),
        headers=headers
    )
    
    return response

if __name__ == "__main__":
    # Test
    res = send_auth_request("test1234", "1.2.3.4", "test")
    print(f"Status: {res.status_code}")
