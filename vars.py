import json

with open('secrets.json') as f:
    config = json.load(f)

api_key = config.get("API_KEY")

music_folder = config.get("MUSIC_FOLDER")
archive_folder = config.get("ARCHIVE_FOLDER")
archives = config.get("ARCHIVES", [])
playlists = config.get("PLAYLISTS", [])
playlist_names = config.get("PLAYLIST_NAMES", [])

# Example secrets.json
"""
    "API_KEY": "API_KEY HERE FROM YOUTUBE",

    "MUSIC_FOLDER": "C:/Users/<user>/Music",
    "ARCHIVE_FOLDER": "C:/Users/<user>/Music/Archive",

    "ARCHIVES": [
        "main.txt",
        "alt.txt",
    ],

    "PLAYLISTS": [
        "https://www.youtube.com/playlist?list=main_playlist",
        "https://www.youtube.com/playlist?list=alt_playlist"
    ],

    "PLAYLIST_NAMES": [
        "main_playlist",
        "alt_playlist"
    ]
"""