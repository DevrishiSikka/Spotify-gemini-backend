from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from openai import OpenAI
import json

app = Flask(__name__)
CORS(app)

# Replace with your actual AIML API key
client = OpenAI(
    base_url="https://api.aimlapi.com/v1",
    api_key="a84731691b2042dcaf203671ac44126e",
)

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
    - title
    - artist
    - album
    - duration (e.g., "4:22")
    - days ago it was added (e.g., "2 days ago")

    Format your entire output strictly as a JSON array of objects.
    User mood: {user_mood}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": master_prompt}]
        )

        raw_text = response.choices[0].message.content.strip()

        # Try to parse the response as JSON
        try:
            playlist_json = json.loads(raw_text)
            return _corsify_actual_response(jsonify(playlist_json))
        except json.JSONDecodeError:
            return _corsify_actual_response(jsonify({
                "error": "Invalid JSON format",
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
