import json
import os

from flask import Flask, jsonify, make_response, render_template, request

import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

ALLOWED_ORIGINS = {
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://harshitappq.onrender.com",

    # 📱 Capacitor Android / iOS
    "capacitor://localhost",
    "http://localhost",
}


# Initialize Firebase once (Render env var first, local file fallback).
if not firebase_admin._apps:
    firebase_config = os.environ.get("FIREBASE_KEY")
    if firebase_config:
        cred = credentials.Certificate(json.loads(firebase_config))
    else:
        cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()


def _format_location(doc):
    data = doc.to_dict() or {}
    created_at = data.get("createdAt")
    created_at_iso = created_at.isoformat() if hasattr(created_at, "isoformat") else None
    return {
        "id": doc.id,
        "name": data.get("name", ""),
        "lat": data.get("lat"),
        "lng": data.get("lng"),
        "address": data.get("address", ""),
        "createdAt": created_at_iso,
    }


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin")
    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Vary"] = "Origin"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.route("/api/locations", methods=["OPTIONS"])
def locations_preflight():
    return make_response("", 204)


@app.route("/api/locations", methods=["GET"])
def list_locations():
    docs = db.collection("user_locations").stream()
    rows = [_format_location(doc) for doc in docs]
    rows.sort(key=lambda item: (item["createdAt"] or ""), reverse=True)
    return jsonify(rows)


@app.route("/api/locations", methods=["POST"])
def save_location():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    address = (payload.get("address") or "").strip()

    if not name:
        return jsonify({"error": "Name is required."}), 400

    try:
        lat = float(payload.get("lat"))
        lng = float(payload.get("lng"))
    except (TypeError, ValueError):
        return jsonify({"error": "Valid lat/lng are required."}), 400

    ref = db.collection("user_locations").document()
    ref.set(
        {
            "name": name,
            "lat": lat,
            "lng": lng,
            "address": address,
            "createdAt": firestore.SERVER_TIMESTAMP,
        }
    )

    return jsonify({"ok": True, "id": ref.id}), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
