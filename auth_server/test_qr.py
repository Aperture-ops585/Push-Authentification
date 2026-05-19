#!/usr/bin/env python3
import sys
import os
import uuid
import time
import requests
import qrcode

# Resolve paths relative to this script's directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from shared import load_config

def main():
    config = load_config()
    if not config:
        print("Error: config.json not found.", file=sys.stderr)
        sys.exit(1)

    web_auth_domain = config.get("rp_id", "web-auth.duckdns.org")
    response_url = config.get("response_url")
    token = config.get("ntfy_token")

    # 1. Generate a unique session ID
    request_id = str(uuid.uuid4())[:8]
    approval_url = f"https://{web_auth_domain}/approve?id={request_id}"

    # 2. Generate and render the QR code in the terminal
    print("\n--- BIOMETRIC QR CODE VERIFICATION ---")
    print("Scan the QR code below with your smartphone to authenticate:")
    
    qr = qrcode.QRCode(version=1, box_size=1, border=2)
    qr.add_data(approval_url)
    qr.make(fit=True)
    
    # Render the QR code in the terminal using ANSI colors
    qr.print_tty()

    print(f"\nVerification Link: {approval_url}")
    print("Waiting for smartphone biometric confirmation...\n")

    # 3. Poll the ntfy server for the phone's decision
    start_time = time.time()
    timeout = 60
    verified = False

    try:
        while time.time() - start_time < timeout:
            # Poll the response topic
            poll_url = f"{response_url}/json?poll=1&since={int(start_time)}"
            headers = {"Authorization": f"Bearer {token}"}
            
            try:
                res = requests.get(poll_url, headers=headers, timeout=5)
                if res.status_code == 200:
                    for line in res.text.strip().split('\n'):
                        if not line:
                            continue
                        data = requests.structures.CaseInsensitiveDict(res.headers) # standard safety
                        # Parse individual message payload
                        payload = requests.utils.get_unicode_from_response(res)
                        
                        # Process polling lines
                        import json
                        parsed_line = json.loads(line)
                        msg = parsed_line.get("message", "")
                        
                        if f"approved:{request_id}" == msg:
                            print("Verification successful! Access GRANTED.")
                            verified = True
                            break
                        elif f"denied:{request_id}" == msg:
                            print("Verification denied by user. Access REJECTED.")
                            sys.exit(1)
            except Exception:
                pass

            if verified:
                break
            time.sleep(2)

        if not verified:
            print("Verification timed out. Access REJECTED.")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nVerification cancelled by user.")
        sys.exit(1)

if __name__ == "__main__":
    main()
