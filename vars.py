import json

deleteVideos = True

with open('secrets.json') as f:
    config = json.load(f)

api_key = config.get("API_KEY")

channel_name = config.get("CHANNEL_NAME")

music_folder = config.get("MUSIC_FOLDER")
m3u8_folder = config.get("M3U8_FOLDER")
archive = config.get("ARCHIVE")

playlists = config.get("PLAYLISTS", [])
playlist_names = config.get("PLAYLIST_NAMES", [])

# Example secrets.json
"""
    "API_KEY": "API_KEY HERE FROM YOUTUBE",

    "MUSIC_FOLDER": "C:/Users/<user>/Music",
    "M3U8_FOLDER": "C:/Users/<user>/Music/Archive",
    "ARCHIVE": "main.txt",

    "PLAYLISTS": [
        "https://www.youtube.com/playlist?list=main_playlist",
        "https://www.youtube.com/playlist?list=alt_playlist"
    ],

    "PLAYLIST_NAMES": [
        "main_playlist",
        "alt_playlist"
    ]
"""