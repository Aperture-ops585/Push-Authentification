import os
import json
from flask import Blueprint, request, jsonify
from webauthn import (
    generate_registration_options,
    verify_registration_response,
    options_to_json
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    AuthenticatorAttachment
)
from webauthn.helpers import bytes_to_base64url
from shared import (
    PROJECT_PATH,
    RP_ID,
    RP_NAME,
    ORIGIN,
    ACTIVE_CHALLENGES,
    save_credential
)

registration_bp = Blueprint("registration", __name__)

@registration_bp.route("/register")
def serve_register_page():
    register_html_path = os.path.join(PROJECT_PATH, "register.html")
    if os.path.exists(register_html_path):
        with open(register_html_path, "r") as f:
            return f.read()
    return "register.html not found on server", 404

@registration_bp.route("/api/register/options")
def register_options():
    authenticator_selection = AuthenticatorSelectionCriteria(
        authenticator_attachment=AuthenticatorAttachment.PLATFORM
    )
    options = generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_id=b"user_aperture",
        user_name="aperture",
        user_display_name="Aperture User",
        authenticator_selection=authenticator_selection
    )
    
    # Store challenge locally to verify later
    ACTIVE_CHALLENGES["register"] = options.challenge
    
    # Convert binary properties to base64url for JSON response
    options_json = json.loads(options_to_json(options))
    return jsonify(options_json)

@registration_bp.route("/api/register/verify", methods=["POST"])
def register_verify():
    challenge = ACTIVE_CHALLENGES.get("register")
    if not challenge:
        return "No challenge generated", 400
        
    try:
        registration_verification = verify_registration_response(
            credential=request.json,
            expected_challenge=challenge,
            expected_origin=ORIGIN,
            expected_rp_id=RP_ID
        )
        
        # Save the generated Credential ID & Public Key
        save_credential(
            cred_id=bytes_to_base64url(registration_verification.credential_id),
            public_key=bytes_to_base64url(registration_verification.credential_public_key),
            sign_count=registration_verification.sign_count
        )
        
        ACTIVE_CHALLENGES.pop("register", None)
        return "Registration Success!", 200
    except Exception as e:
        return f"Registration Verification Failed: {str(e)}", 400
