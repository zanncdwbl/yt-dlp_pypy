import os, yt_dlp, requests
from defs import *
from vars import *

class loggerOutput(object):
    def debug(self, msg):
        # print("Captured Log:", msg)
        pass

    def warning(self, msg):
        # print("Captured Warning:", msg)
        pass

    def error(self, msg):
        print("Captured Error:", msg)

def hook(d):
    file_name = os.path.basename(d["filename"])
    if d["status"] == "finished":
        print("\nFinishing:", file_name)
        print("-" * 40)
    elif d["status"] == "error":
        print(f"Failed to download: {d.get("filename", "Unknown")} - {d["message"]}")

ydl_opts_main = {
    "outtmpl": os.path.join(music_folder, "%(title)s.%(ext)s"),
    "writethumbnail": True,
    "embedthumbnail": True,
    "ignoreerrors": True,
    "playlistreverse": True,
    "format": "251/bestaudio[ext=m4a]",
    "verbose": True,
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "opus",
            "preferredquality": "0",
        },
        {
            "key": "FFmpegVideoRemuxer",
            "preferedformat": "opus"
        },
        {
            "key": "FFmpegThumbnailsConvertor",
            "format": "jpg",
        },
        {
            "key": "FFmpegMetadata",
            "add_metadata": True
        },
        {
            "key": "EmbedThumbnail",
            "already_have_thumbnail": False
        },
    ],
    "logger": loggerOutput(),
    "progress_hooks": [hook],
}

# Iterate over x playlists from json, make sure that the lists are actually the same size, or else the loop breaks
for i, (archive, playlist, playlist_name) in enumerate(zip(archives, playlists, playlist_names)):
    print(f"Processing playlist: {playlist_name}\n\n")
    
    ydl_opts = ydl_opts_main.copy()
    ydl_opts['download_archive'] = archive

    processed_entries, deleted_entries = get_playlist_info([playlist])
    # add command here to paste out all deleted entries, easier for keeping track

    if i[0]: # Assuming main playlist is index 0
        try:
            check_titles(processed_entries)
        except DuplicateTitle as e:
            print(e)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([playlist])
    else:
        #do flat playlist stuff here, api call etc
        print()