from flask import Flask
from registration import registration_bp
from authentication import authentication_bp

app = Flask(__name__)

# Register Blueprints for modular route management
app.register_blueprint(registration_bp)
app.register_blueprint(authentication_bp)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
