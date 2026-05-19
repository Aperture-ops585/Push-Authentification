#!/usr/bin/env python3
# python script for ntfy pam authentication, can be enabled by inserting the following line in the pam file:
# auth     required    pam_exec.so     expose_authtok      /path/to/pam_ssh_ntfy.py
# Usually after a password login enabling 2FA, i.e @include common-auth
import os
import sys
import time
import uuid
import json
import requests

# Import the updated ntfy_auth logic — resolve path relative to this script
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from ntfy_auth import send_auth_request, load_config

# Configuration
CONFIG = load_config()
TOPIC_URL = CONFIG["topic_url"]
RESPONSE_URL = CONFIG["response_url"]
NTFY_TOKEN = CONFIG["ntfy_token"]
TIMEOUT = 60 

PAM_USER = os.getenv("PAM_USER", "unknown_user")
# For sudo, RHOST is often empty. Fallback to 'local machine' for clarity in push.
PAM_RHOST = os.getenv("PAM_RHOST") or "local machine"
PAM_SERVICE = os.getenv("PAM_SERVICE", "unknown_service")

def poll_for_decision(request_id, start_time):
    """
    Polls the ntfy server for messages on the response topic.
    """
    # Use the response_url defined in the config
    poll_url = f"{RESPONSE_URL}/json?poll=1&since={int(start_time)}"
    
    try:
        headers = {"Authorization": f"Bearer {NTFY_TOKEN}"}
        response = requests.get(poll_url, headers=headers, timeout=5)
        if response.status_code == 200:
            for line in response.text.strip().split('\n'):
                if not line: continue
                data = json.loads(line)
                message = data.get("message", "") #The message is the response from the phone (approved:req_...). 
                
                if f"approved:{request_id}" == message:
                    return "approved"
                if f"denied:{request_id}" == message:
                    return "denied"
    except Exception:
        pass
    return None

def main():
    request_id = str(uuid.uuid4())[:8] #Generate a unique request ID. 
    
    start_time = time.time()

    # 1. Send the Push Notification
    try:
        response = send_auth_request(request_id, PAM_RHOST, PAM_SERVICE)
        if response.status_code != 200:
            sys.exit(1) # Fail closed
    except Exception:
        sys.exit(1) # Fail closed

    # 2. Poll ntfy for the decision
    while time.time() - start_time < TIMEOUT:
        decision = poll_for_decision(request_id, start_time)
        if decision == "approved":
            sys.exit(0)
        elif decision == "denied":
            print("\nBiometric verification bypassed. Requesting password...", file=sys.stderr)
            sys.exit(1)
        
        time.sleep(2) # Wait 2 seconds between polls

    # 3. Timeout
    print("\nBiometric verification timed out. Requesting password...", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    main()
