import os
import json
import requests
from flask import Blueprint, request, jsonify
from webauthn import (
    generate_authentication_options,
    verify_authentication_response,
    options_to_json
)
from webauthn.helpers.structs import PublicKeyCredentialDescriptor
from webauthn.helpers import base64url_to_bytes
from shared import (
    PROJECT_PATH,
    RP_ID,
    ORIGIN,
    CONFIG_FILE,
    ACTIVE_CHALLENGES,
    load_credential,
    save_credential
)

authentication_bp = Blueprint("authentication", __name__)

@authentication_bp.route("/approve")
def serve_approve_page():
    approve_html_path = os.path.join(PROJECT_PATH, "approve.html")
    if os.path.exists(approve_html_path):
        with open(approve_html_path, "r") as f:
            return f.read()
    return "approve.html not found on server", 404

@authentication_bp.route("/api/auth/options")
def auth_options():
    req_id = request.args.get("id")
    cred = load_credential()
    if not cred:
        return "No registered credential. Please go to /register first.", 400
        
    options = generate_authentication_options(
        rp_id=RP_ID,
        allow_credentials=[PublicKeyCredentialDescriptor(
            id=base64url_to_bytes(cred["id"])
        )]
    )
    
    # Store the unique challenge indexed by request_id
    ACTIVE_CHALLENGES[req_id] = options.challenge
    
    options_json = json.loads(options_to_json(options))
    return jsonify(options_json)

@authentication_bp.route("/api/auth/verify", methods=["POST"])
def auth_verify():
    req_id = request.args.get("id")
    challenge = ACTIVE_CHALLENGES.get(req_id)
    cred = load_credential()
    
    if not challenge or not cred:
        return "Invalid session/request", 400
        
    try:
        # Cryptographically verify the biometric signature sent by the phone browser
        auth_verification = verify_authentication_response(
            credential=request.json,
            expected_challenge=challenge,
            expected_origin=ORIGIN,
            expected_rp_id=RP_ID,
            credential_public_key=base64url_to_bytes(cred["public_key"]),
            credential_current_sign_count=cred["sign_count"]
        )
        
        # Update signature count in DB
        save_credential(cred["id"], cred["public_key"], auth_verification.new_sign_count)
        
        # 1. Success! Publish approval payload to ntfy server response topic
        # (This is what pam_ssh_ntfy.py is actively polling for!)
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            
        requests.post(
            config["response_url"],
            data=f"approved:{req_id}",
            headers={"Authorization": f"Bearer {config['ntfy_token']}"}
        )
        
        # Clean up challenge
        ACTIVE_CHALLENGES.pop(req_id, None)
        return "Unlock Verified!", 200
        
    except Exception as e:
        return f"Authentication Failed: {str(e)}", 401
