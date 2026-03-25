#!/usr/bin/env python3
"""
NODO One — Servidor local para demo en vivo
Ejecutar: python3 server.py
Luego abrir: http://localhost:3000
"""

import os
import json
import urllib.request
import urllib.error
from flask import Flask, request, jsonify, send_from_directory

# ─── CONFIGURACIÓN ─────────────────────────────────────────
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_KEY", "")
PORT = int(os.environ.get("PORT", 3000))
# ────────────────────────────────────────────────────────────

app = Flask(__name__, static_folder="public")


@app.route("/")
def index():
    return send_from_directory("public", "index.html")


@app.route("/api/chat", methods=["POST"])
def chat_proxy():
    """Proxy seguro a la API de Anthropic — la clave nunca sale al navegador."""
    try:
        payload = request.get_json(force=True)
        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=data,
            headers={
                "Content-Type": "application/json",
                "x-api-key": ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return jsonify(result)

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            err = json.loads(body)
        except Exception:
            err = {"error": {"message": body}}
        return jsonify(err), e.code
    except Exception as ex:
        return jsonify({"error": {"message": str(ex)}}), 500


if __name__ == "__main__":
    print(f"\n{'─'*52}")
    print(f"  NODO One · Demo en vivo")
    print(f"  http://localhost:{PORT}")
    print(f"{'─'*52}\n")
    app.run(host="0.0.0.0", port=PORT, debug=False)
