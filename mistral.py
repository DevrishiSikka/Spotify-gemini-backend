from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import json
import re
import ast
from mistralai import Mistral

app = Flask(__name__)
CORS(app, origins="*")

# Global CORS Headers
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
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

Return only a JSON array with no additional text, formatting, or explanation. The response should be valid JSON that can be parsed directly.
Format:
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
        # Initialize Mistral client
        with Mistral(api_key="AYVGzIu6L5X6bxHVGbjBmprpr3IzqLmV") as mistral_client:
            # Call Mistral AI API
            response = mistral_client.chat.complete(
                model="mistral-small-latest",  # You can also use "mistral-medium-latest" or "mistral-large-latest"
                messages=[
                    {
                        "content": master_prompt,
                        "role": "user",
                    },
                ]
            )

            # Get the response content
            raw_text = response.choices[0].message.content.strip()

            # Extract JSON from the response
            # First, look for JSON between code blocks
            import re
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', raw_text)
            
            if json_match:
                # If JSON is wrapped in code blocks, extract it
                json_str = json_match.group(1).strip()
            else:
                # Otherwise use the whole text and try to find JSON
                json_str = raw_text
                
                # Try to find array or object in the text
                array_match = re.search(r'\[\s*\{.*\}\s*\]', json_str, re.DOTALL)
                if array_match:
                    json_str = array_match.group(0)
                else:
                    object_match = re.search(r'\{\s*".*"\s*:.*\}', json_str, re.DOTALL)
                    if object_match:
                        json_str = object_match.group(0)

            # Try parsing with json
            try:
                playlist_json = json.loads(json_str)
                return _corsify_actual_response(jsonify(playlist_json))
            except json.JSONDecodeError:
                # Fallback: try literal_eval for semi-valid Python lists
                try:
                    playlist_json = ast.literal_eval(json_str)
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
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
    response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
    return response

def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

if __name__ == "__main__":
    app.run(debug=True, port=5000)