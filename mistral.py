# from flask import Flask, request, jsonify, make_response
# from flask_cors import CORS
# import json
# import re
# import ast
# from mistralai import Mistral

# app = Flask(__name__)
# CORS(app, origins="*")

# # Global CORS Headers
# @app.after_request
# def add_cors_headers(response):
#     response.headers['Access-Control-Allow-Origin'] = '*'
#     response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
#     response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
#     return response

# @app.route("/api/generate", methods=["POST", "OPTIONS"])
# def generate_playlist():
#     if request.method == "OPTIONS":
#         return _build_cors_preflight_response()

#     data = request.get_json()
#     user_mood = data.get("mood", "")

#     master_prompt = f"""
# You are a music recommendation assistant. Based on the user's mood or input, generate a playlist of EXACTLY 10 DIFFERENT songs.

# CRITICAL REQUIREMENTS:
# 1. ONLY recommend REAL songs that actually exist - check your knowledge carefully
# 2. Each song MUST be COMPLETELY UNIQUE - no duplicates in artist or title combinations in the playlist
# 3. Verify each song is by the correct artist before including it
# 4. DO NOT REPEAT the same artist more than twice in the playlist

# Each song should include:
# - title: name of the song
# - artist: artist or group name
# - album: the album it belongs to
# - duration: estimated song length (e.g., "4:22")
# - days: how long ago it was added (e.g., "2 days ago", "1 week ago")

# Return only a JSON array with no additional text, formatting, or explanation. The response should be valid JSON that can be parsed directly.
# Format:
# [
#   {{
#     "title": "Song Title",
#     "artist": "Artist Name",
#     "album": "Album Name",
#     "duration": "Song Duration",
#     "days": "Days the song was added"
#   }}
# ]

# Before finalizing your response, triple-check each song to confirm:
# 1. This is a real song by this artist - do not include made-up songs
# 2. This song has not been included previously in this playlist
# 3. The album name is correct for this song
# 4. You have included exactly 10 different songs
# 5. No artist appears more than twice in the playlist

# User mood: {user_mood}
# """

#     try:
#         # Initialize Mistral client
#         with Mistral(api_key="AYVGzIu6L5X6bxHVGbjBmprpr3IzqLmV") as mistral_client:
#             # Call Mistral AI API
#             response = mistral_client.chat.complete(
#                 model="mistral-medium-latest",  # Using medium model for better knowledge of real songs
#                 messages=[
#                     {
#                         "content": master_prompt,
#                         "role": "user",
#                     },
#                 ],
#                 temperature=0.8,  # Balanced temperature for factual responses with variety
#                 max_tokens=2048,  # Ensure enough tokens for a complete response
#                 top_p=0.9         # Slightly constrained sampling for higher quality
#             )

#             # Get the response content
#             raw_text = response.choices[0].message.content.strip()

#             # Extract JSON from the response
#             # First, look for JSON between code blocks
#             import re
#             json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', raw_text)
            
#             if json_match:
#                 # If JSON is wrapped in code blocks, extract it
#                 json_str = json_match.group(1).strip()
#             else:
#                 # Otherwise use the whole text and try to find JSON
#                 json_str = raw_text
                
#                 # Try to find array or object in the text
#                 array_match = re.search(r'\[\s*\{.*\}\s*\]', json_str, re.DOTALL)
#                 if array_match:
#                     json_str = array_match.group(0)
#                 else:
#                     object_match = re.search(r'\{\s*".*"\s*:.*\}', json_str, re.DOTALL)
#                     if object_match:
#                         json_str = object_match.group(0)

#             # Try parsing with json
#             try:
#                 playlist_json = json.loads(json_str)
                
#                 # Additional validation to check for duplicates
#                 if isinstance(playlist_json, list):
#                     # Check for duplicate songs
#                     seen_songs = set()
#                     unique_playlist = []
                    
#                     for song in playlist_json:
#                         # Create a unique identifier for each song
#                         song_id = f"{song.get('title', '').lower()}|{song.get('artist', '').lower()}"
                        
#                         if song_id not in seen_songs:
#                             seen_songs.add(song_id)
#                             unique_playlist.append(song)
                    
#                     # If we've removed duplicates but still have fewer than 10 songs,
#                     # we'll try with a different model or higher temperature if unique_playlist is too small
#                     if len(unique_playlist) < 5 and len(unique_playlist) < len(playlist_json):
#                         # Try again with the medium model and higher temperature
#                         retry_response = mistral_client.chat.complete(
#                             model="mistral-medium-latest",  # Upgrade to a more capable model
#                             messages=[
#                                 {
#                                     "content": master_prompt + "\n\nIMPORTANT: Ensure ALL 10 songs are DIFFERENT. Do not repeat any songs!",
#                                     "role": "user",
#                                 },
#                             ],
#                             temperature=0.9,  # Higher temperature for more variety
#                             max_tokens=2048
#                         )
                        
#                         retry_text = retry_response.choices[0].message.content.strip()
                        
#                         # Process the retry response
#                         json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', retry_text)
#                         if json_match:
#                             retry_json_str = json_match.group(1).strip()
#                         else:
#                             retry_json_str = retry_text
#                             array_match = re.search(r'\[\s*\{.*\}\s*\]', retry_json_str, re.DOTALL)
#                             if array_match:
#                                 retry_json_str = array_match.group(0)
                        
#                         try:
#                             retry_playlist = json.loads(retry_json_str)
#                             if isinstance(retry_playlist, list):
#                                 # Check for duplicates again
#                                 for song in retry_playlist:
#                                     song_id = f"{song.get('title', '').lower()}|{song.get('artist', '').lower()}"
#                                     if song_id not in seen_songs:
#                                         seen_songs.add(song_id)
#                                         unique_playlist.append(song)
#                         except:
#                             # If retry fails, we'll continue with what we have
#                             pass
                    
#                     # Always return the raw playlist without any wrapper or warnings
#                     return _corsify_actual_response(jsonify(unique_playlist))
                
#                 return _corsify_actual_response(jsonify(playlist_json))
                
#             except json.JSONDecodeError:
#                 # Fallback: try literal_eval for semi-valid Python lists
#                 try:
#                     playlist_json = ast.literal_eval(json_str)
#                     return _corsify_actual_response(jsonify(playlist_json))
#                 except Exception:
#                     return _corsify_actual_response(jsonify({
#                         "error": "Invalid JSON format from model",
#                         "raw_output": raw_text
#                     })), 500

#     except Exception as e:
#         return _corsify_actual_response(jsonify({"error": str(e)})), 500

# @app.route("/api/generate-name", methods=["POST", "OPTIONS"])
# def generate_playlist_name():
#     if request.method == "OPTIONS":
#         return _build_cors_preflight_response()

#     data = request.get_json()
#     user_prompt = data.get("prompt", "")

#     name_prompt = f"""
# Generate a catchy, memorable playlist name based on this user input: "{user_prompt}"

# REQUIREMENTS:
# 1. The name must be AT MOST 4 words (fewer words is better)
# 2. The name should capture the essence or mood of the user's prompt
# 3. Be creative, evocative, and original
# 4. Don't use generic phrases like "Music for..." or "Songs for..."

# Return ONLY the playlist name as plain text with no quotes, explanations, or additional formatting.
# """

#     try:
#         # Initialize Mistral client
#         with Mistral(api_key="AYVGzIu6L5X6bxHVGbjBmprpr3IzqLmV") as mistral_client:
#             # Call Mistral AI API
#             response = mistral_client.chat.complete(
#                 model="mistral-small-latest",  # Small model is sufficient for naming
#                 messages=[
#                     {
#                         "content": name_prompt,
#                         "role": "user",
#                     },
#                 ],
#                 temperature=0.9,  # Higher temperature for creativity
#                 max_tokens=20,    # Short response
#                 top_p=0.95        # Allow for creative sampling
#             )

#             # Get the response content
#             raw_text = response.choices[0].message.content.strip()
            
#             # Process the response to ensure it's at most 4 words
#             words = raw_text.split()
#             if len(words) > 4:
#                 # Truncate to 4 words if needed
#                 playlist_name = " ".join(words[:4])
#             else:
#                 playlist_name = raw_text
            
#             # Remove any quotes or punctuation at the beginning or end
#             playlist_name = playlist_name.strip('"\'.,!?:;()[]{}')
            
#             # Return just the name as plain text in JSON format
#             return _corsify_actual_response(jsonify(playlist_name))

#     except Exception as e:
#         return _corsify_actual_response(jsonify({"error": str(e)})), 500

# def _build_cors_preflight_response():
#     response = make_response()
#     response.headers.add("Access-Control-Allow-Origin", "*")
#     response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
#     response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
#     return response

# def _corsify_actual_response(response):
#     response.headers.add("Access-Control-Allow-Origin", "*")
#     return response

# if __name__ == "__main__":
#     app.run(debug=True, port=5000)


from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import json
import re
import ast
import random
from mistralai import Mistral

app = Flask(__name__)
CORS(app, origins="*")


song_titles = [
    "Blinding Lights", "Levitating", "Shape of You", "Bad Guy", "Stay", "Uptown Funk", "Rolling in the Deep",
    "Billie Jean", "Thinking Out Loud", "Take On Me", "Happier Than Ever", "Peaches", "As It Was",
    "Anti-Hero", "Drivers License", "Radioactive", "Counting Stars", "Sunflower", "Watermelon Sugar",
    "Industry Baby", "Save Your Tears", "Senorita", "Believer", "Memories", "Perfect", "Positions",
    "Shivers", "Good 4 U", "Lovely", "Goosebumps", "Rockstar", "Lose Yourself", "Numb", "Starboy",
    "Circles", "Lucid Dreams", "See You Again", "WAP", "Laugh Now Cry Later", "Don't Start Now"
]

artist_names = [
    "The Weeknd", "Dua Lipa", "Ed Sheeran", "Billie Eilish", "Justin Bieber", "Bruno Mars", "Adele",
    "Michael Jackson", "a-ha", "Olivia Rodrigo", "Taylor Swift", "Harry Styles", "Drake", "Post Malone",
    "Imagine Dragons", "Eminem", "Linkin Park", "SZA", "Doja Cat", "Travis Scott", "Khalid", "Juice WRLD",
    "Katy Perry", "OneRepublic", "Maroon 5", "Ariana Grande", "Camila Cabello", "Bad Bunny", "Lizzo",
    "Shawn Mendes", "21 Savage", "Nicki Minaj", "Lady Gaga"
]

album_names = [
    "After Hours", "Future Nostalgia", "÷ (Divide)", "Happier Than Ever", "Justice", "Thriller",
    "Midnights", "Hollywood's Bleeding", "Scorpion", "25", "Positions", "Starboy", "Fine Line",
    "When We All Fall Asleep, Where Do We Go?", "x", "The Eminem Show", "Lover", "Goodbye & Good Riddance"
]


def generate_random_duration():
    minutes = random.randint(2, 5)
    seconds = random.randint(0, 59)
    return f"{minutes}:{seconds:02d}"

def generate_random_song():
    return {
        "title": random.choice(song_titles),
        "artist": random.choice(artist_names),
        "album": random.choice(album_names),
        "duration": generate_random_duration(),
        "days": f"{random.randint(1, 7)} days ago"
    }


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
You are a music recommendation assistant. Based on the user's mood or input, generate a playlist of EXACTLY 10 DIFFERENT songs.

CRITICAL REQUIREMENTS:
1. ONLY recommend REAL songs that actually exist - check your knowledge carefully
2. Each song MUST be COMPLETELY UNIQUE - no duplicates in artist or title combinations in the playlist
3. Verify each song is by the correct artist before including it
4. DO NOT REPEAT the same artist more than twice in the playlist

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

Before finalizing your response, triple-check each song to confirm:
1. This is a real song by this artist - do not include made-up songs
2. This song has not been included previously in this playlist
3. The album name is correct for this song
4. You have included exactly 10 different songs
5. No artist appears more than twice in the playlist

User mood: {user_mood}
"""

    try:
        with Mistral(api_key="AYVGzIu6L5X6bxHVGbjBmprpr3IzqLmV") as mistral_client:
            response = mistral_client.chat.complete(
                model="mistral-medium-latest",
                messages=[
                    {
                        "content": master_prompt,
                        "role": "user",
                    },
                ],
                temperature=0.8,
                max_tokens=2048,
                top_p=0.9
            )

            raw_text = response.choices[0].message.content.strip()

            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', raw_text)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                json_str = raw_text
                array_match = re.search(r'\[\s*\{.*\}\s*\]', json_str, re.DOTALL)
                if array_match:
                    json_str = array_match.group(0)
                else:
                    object_match = re.search(r'\{\s*".*"\s*:.*\}', json_str, re.DOTALL)
                    if object_match:
                        json_str = object_match.group(0)

            try:
                playlist_json = json.loads(json_str)
                if isinstance(playlist_json, list):
                    seen_songs = set()
                    unique_playlist = []

                    for song in playlist_json:
                        song_id = f"{song.get('title', '').lower()}|{song.get('artist', '').lower()}"
                        if song_id not in seen_songs:
                            seen_songs.add(song_id)
                            unique_playlist.append(song)

                    if len(unique_playlist) < 5 and len(unique_playlist) < len(playlist_json):
                        retry_response = mistral_client.chat.complete(
                            model="mistral-medium-latest",
                            messages=[
                                {
                                    "content": master_prompt + "\n\nIMPORTANT: Ensure ALL 10 songs are DIFFERENT. Do not repeat any songs!",
                                    "role": "user",
                                },
                            ],
                            temperature=0.9,
                            max_tokens=2048
                        )

                        retry_text = retry_response.choices[0].message.content.strip()
                        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', retry_text)
                        if json_match:
                            retry_json_str = json_match.group(1).strip()
                        else:
                            retry_json_str = retry_text
                            array_match = re.search(r'\[\s*\{.*\}\s*\]', retry_json_str, re.DOTALL)
                            if array_match:
                                retry_json_str = array_match.group(0)

                        try:
                            retry_playlist = json.loads(retry_json_str)
                            if isinstance(retry_playlist, list):
                                for song in retry_playlist:
                                    song_id = f"{song.get('title', '').lower()}|{song.get('artist', '').lower()}"
                                    if song_id not in seen_songs:
                                        seen_songs.add(song_id)
                                        unique_playlist.append(song)
                        except:
                            pass

                    return _corsify_actual_response(jsonify(unique_playlist))

                return _corsify_actual_response(jsonify(playlist_json))

            except json.JSONDecodeError:
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

@app.route("/songs", methods=["GET"])
def get_random_songs():
    num_songs = 50
    generated = []
    used_titles = set()

    while len(generated) < num_songs:
        song = generate_random_song()
        key = (song["title"], song["artist"])  # avoid exact duplicates
        if key not in used_titles:
            generated.append(song)
            used_titles.add(key)

    return jsonify(generated)

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
