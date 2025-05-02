from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import requests
import json

app = Flask(__name__)
CORS(app)

GEMINI_API_KEY = "AIzaSyBU2NkGo5f4n7BGhcg3tlWrd3s-uyJWPUc"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# CORS headers
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = 'https://silver-fortnight-q6v7grr5r76h6r5-3000.app.github.dev'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

@app.route("/api/generate", methods=["POST", "OPTIONS"])
def generate_playlist():
    if request.method == "OPTIONS":
        return _build_cors_preflight_response()

    data = request.get_json()
    user_mood = data.get("mood", "")

    master_prompt = f"""
    You are a music recommendation assistant. Based on the user's mood or input, generate a playlist of 10 songs.
    Each song should include:
    - title: name of the song
    - artist: artist or group name
    - album: the album it belongs to
    - duration: estimated song length (e.g., "4:22")
    - days: how long ago it was added (e.g., "2 days ago", "1 week ago")

    Return the data strictly in the following JSON format:
    [
      {{
        "title": "Song Title",
        "artist": "Artist Name",
        "album": "Album Name",
        "duration": "Song Duration",
        "days": "Days the song was added"
      }}
    ]

    User mood: {user_mood}
    """

    payload = {
        "contents": [
            {
                "parts": [
                    { "text": master_prompt }
                ]
            }
        ]
    }

    try:
        response = requests.post(
            GEMINI_URL,
            headers={"Content-Type": "application/json"},
            params={"key": GEMINI_API_KEY},
            json=payload
        )
        response.raise_for_status()
        gemini_data = response.json()

        # Extract and parse Gemini's text response
        raw_text = gemini_data.get("candidates", [])[0].get("content", {}).get("parts", [])[0].get("text", "")
        try:
            playlist_json = json.loads(raw_text)
            return _corsify_actual_response(jsonify(playlist_json))
        except json.JSONDecodeError:
            return _corsify_actual_response(jsonify({
                "error": "Invalid JSON response from model",
                "raw_output": raw_text
            })), 500

    except requests.exceptions.RequestException as e:
        return _corsify_actual_response(jsonify({"error": str(e)})), 500

def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "https://silver-fortnight-q6v7grr5r76h6r5-3000.app.github.dev")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
    response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
    return response

def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "https://silver-fortnight-q6v7grr5r76h6r5-3000.app.github.dev")
    return response

if __name__ == "__main__":
    app.run(debug=True, port=5000)
