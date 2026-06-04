import os
import socket
from http import HTTPStatus

from flask import Flask, jsonify


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def index():
        return jsonify(
            {
                "app": os.getenv("APP_NAME", "devops-k8s-demo"),
                "environment": os.getenv("APP_ENV", "local"),
                "version": os.getenv("APP_VERSION", "0.1.0"),
                "hostname": socket.gethostname(),
                "secretConfigured": bool(os.getenv("DEMO_SECRET_TOKEN")),
            }
        )

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), HTTPStatus.OK

    return app


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    create_app().run(host="0.0.0.0", port=port)
