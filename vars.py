import json

with open('secrets.json') as f:
    config = json.load(f)

api_key = config.get("API_KEY")

music_folder = config.get("MUSIC_FOLDER")
archive_folder = config.get("ARCHIVE_FOLDER")
archives = config.get("ARCHIVES", [])
playlists = config.get("PLAYLISTS", [])
playlist_names = config.get("PLAYLIST_NAMES", [])