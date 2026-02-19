from flask import Flask, jsonify, render_template, request
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

app = Flask(__name__)

# 🔐 Load Firebase key securely from Render Environment Variable
firebase_config = os.environ.get("FIREBASE_KEY")

if not firebase_admin._apps:
    if not firebase_config:
        raise Exception("FIREBASE_KEY environment variable not set!")

    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)

db = firestore.client()


# 🧠 Helper: Format Firestore document
def _format_location(doc):
    data = doc.to_dict() or {}
    created_at = data.get("createdAt")

    # Convert Firestore timestamp to ISO string
    created_at_iso = (
        created_at.isoformat() if hasattr(created_at, "isoformat") else None
    )

    return {
        "id": doc.id,
        "name": data.get("name", ""),
        "lat": data.get("lat"),
        "lng": data.get("lng"),
        "address": data.get("address", ""),
        "createdAt": created_at_iso,
    }





# 📍 Get all saved locations
@app.route("/api/locations", methods=["GET"])
def list_locations():
    docs = db.collection("user_locations").stream()
    rows = [_format_location(doc) for doc in docs]

    # Sort newest first
    rows.sort(key=lambda item: (item["createdAt"] or ""), reverse=True)

    return jsonify(rows)


# 📌 Save new location
@app.route("/api/locations", methods=["POST"])
def save_location():
    payload = request.get_json(silent=True) or {}

    name = (payload.get("name") or "").strip()
    address = (payload.get("address") or "").strip()

    if not name:
        return jsonify({"error": "Name is required."}), 400

    # Validate lat/lng
    try:
        lat = float(payload.get("lat"))
        lng = float(payload.get("lng"))
    except (TypeError, ValueError):
        return jsonify({"error": "Valid lat/lng are required."}), 400

    # Save to Firestore
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


# 🚀 Run locally (Render ignores this block)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
