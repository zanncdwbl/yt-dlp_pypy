import os, yt_dlp
from defs import *

class loggerOutput(object):
    def debug(self, msg):
        # print("Captured Log:", msg)
        pass

    def warning(self, msg):
        # print("Captured Warning:", msg)
        pass

    def error(self, msg):
        print("Captured Error:", msg)
        pass

def hook(d):
    file_name = os.path.basename(d["filename"])
    if d["status"] == "finished":
        print("\nFinishing:", file_name)
        print("-" * 40)

ydl_opts_main = {
    "outtmpl": os.path.join(music_folder, "%(title)s.%(ext)s"),
    # "cookiesfrombrowser": "firefox",
    "sleep_interval": 10, # just so youtube cries or something
    "download_archive": archive,
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

credentials = authenticate_with_oauth()
access_token = credentials.token

headers = {"Authorization": f"Bearer {access_token}"}

# #Iterate over x playlists from json, make sure that the lists are actually the same size, or else the loop breaks
for i, (playlist_url, playlist_name) in enumerate(zip(playlists, playlist_names)):
    ydl_opts = ydl_opts_main.copy()
    video_ids = yt_flat_playlist(playlist_url, playlist_name)

    if i == 0: # Assuming main playlist is index 0
        available_videos, deleted_ids = get_playlist_info(playlist_name, headers, video_ids)

    try:
        check_titles(playlist_name, available_videos)
    except DuplicateTitle as e:
        print(e)
        break

    if deleteVideos:
        delete_deletedVidoes(playlist_url, headers, deleted_ids)
    else:
        if i == 0:
            print("Completed processing, beginning download.")
        else:
            print("Completed processing, beginning m3u8 creation.")

    if i == 0:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([playlist_url])
    else:
        generate_playlist(m3u8_folder, playlist_name, available_videos, video_ids)

    try:
        os.remove("thumbnail.png")
    except FileNotFoundError:
        print("Thumbnail not found, skipping removal.")