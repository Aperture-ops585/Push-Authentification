# ntfy-PAM Auth
Biometric-based authentication for SSH, Sudo, etc.

## 1. Deploy ntfy (Docker)
```bash
# Start server
docker-compose up -d

# Configure auth
docker exec -it ntfy ntfy user add --role=admin admin
docker exec -it ntfy ntfy user change-pass admin
docker exec -it ntfy ntfy token add admin
docker exec -it ntfy ntfy access '*' '<ntfy_response_topic>' write-only
```

## 2. Configure App
Rename `config.json.example` to `config.json` and customize your configuration parameters:
```json
{
  "ntfy_token": "<your_ntfy_token>",
  "topic_url": "https://<your_ntfy_domain>/<ntfy_auth_topic>",
  "response_url": "https://<your_ntfy_domain>/<ntfy_response_topic>",
  "project_path": "/home/<user>/Auth/auth_server",
  "rp_id": "<your_webauthn_domain>",
  "rp_name": "<your_relying_party_name>",
  "rp_origin": "https://<your_webauthn_domain>"
}
```

## 3. Enable PAM
Add to `/etc/pam.d/sshd` or `/etc/pam.d/sudo`:
```bash
auth required pam_exec.so expose_authtok /path/to/pam_ssh_ntfy.py
```

## How it works
1. **Trigger**: Service calls script.
2. **Push**: Notification sent to phone with Approve/Deny buttons.
3. **Reply**: Phone posts response to `<ntfy_response_topic>` (anonymous write).
4. **Grant**: Script polls response and exits 0 on success.

---

## 4. WebAuthn Biometric Server Setup (`auth_server`)

To enable passwordless biometric verification, run the following setup commands on your target server.

### Step A: Install Dependencies
Install Flask, requests, and the `webauthn` v2.x library:
```bash
pip install flask webauthn requests
```

### Step B: Create Systemd User Service
Run these commands to create and configure a persistent background service running under your system user session:

```bash
# 1. Create the systemd user service directory if it doesn't exist
mkdir -p ~/.config/systemd/user/

# 2. Write the service unit file (replace <user> with your system username)
cat << 'EOF' > ~/.config/systemd/user/auth_server.service
[Unit]
Description=WebAuthn Biometric Auth Server
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/<user>/Auth/auth_server
ExecStart=/usr/bin/python3 /home/<user>/Auth/auth_server/auth_server.py
Restart=always
RestartSec=3

[Install]
WantedBy=default.target
EOF
```

### Step C: Enable & Start the Service
Run these commands to reload systemd, enable lingering, and boot the server:
```bash
# Reload systemd user daemon
systemctl --user daemon-reload

# Enable service boot at system startup (without requiring active login session)
loginctl enable-linger $USER

# Start and enable the service
systemctl --user enable --now auth_server

# Verify the status is 'active (running)'
systemctl --user status auth_server
```

---

## 5. Device Registration

Once the service is active behind Nginx, enroll your smartphone or biometric device:
1. Navigate to: `https://<your_webauthn_domain>/register`
2. Click **Register Device**.
3. Scan your fingerprint when prompted by your phone browser.

