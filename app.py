from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import json
import ast
from openai import OpenAI

app = Flask(__name__)
CORS(app)

client = OpenAI(
    base_url="https://api.aimlapi.com/v1",
    api_key="a84731691b2042dcaf203671ac44126e",  # Replace with your actual AIML API key
)

# Global CORS Headers
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

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": master_prompt}]
        )

        raw_text = response.choices[0].message.content.strip()

        # Clean markdown fencing if present
        if raw_text.startswith("```json") or raw_text.startswith("```"):
            raw_text = raw_text.strip("`").split("json")[-1].strip()

        # Try parsing with json
        try:
            playlist_json = json.loads(raw_text)
            return _corsify_actual_response(jsonify(playlist_json))
        except json.JSONDecodeError:
            # Fallback: try literal_eval for semi-valid Python lists
            try:
                playlist_json = ast.literal_eval(raw_text)
                return _corsify_actual_response(jsonify(playlist_json))
            except Exception:
                return _corsify_actual_response(jsonify({
                    "error": "Invalid JSON format from model",
                    "raw_output": raw_text
                })), 500

    except Exception as e:
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
