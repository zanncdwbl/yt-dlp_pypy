import os, re, subprocess, json, requests
from vars import *

class DuplicateTitle(Exception):
    pass

# Used to make sure that even when we use flatplaylist, it will return how the actual downloaded songs are.
def replace_special_characters(title):
    title = re.sub(r'\|', '｜', title)
    title = re.sub(r'"', '＂', title)
    title = re.sub(r'"', '¨', title)
    title = re.sub(r'\?', '？', title)
    title = re.sub(r'/', '⧸', title)
    title = re.sub(r'\*', '＊', title)
    title = re.sub(r':', '：', title)
    return title

# Command line instead of python, gets all of the video metadata, sends it into file, which is processed to get entry info in playlist
def get_playlist_info(playlist_url, unavailable_files = "unavailable.txt", deleted_files = "deleted.txt"):
    command = f'yt-dlp --flat-playlist --dump-single-json -I ::-1 "{playlist_url}"'
    result = subprocess.run(command, text=True, shell=True, capture_output=True, check=True)
    data = json.loads(result.stdout)
    entries = data.get('entries', [])

    available_videos = {}

    for entry in entries:
        title = replace_special_characters(entry.get('title'))
        video_id = entry.get('id')
        duration = entry.get('duration', 0)

        #removed status cause its not really needed if we already parse deleted/private etc in flat
        req = requests.get(f'https://www.googleapis.com/youtube/v3/videos?id={video_id}&part=contentDetails,snippet&key={api_key}') # remove snippet if you dont have any private songs uploaded
        apidata = req.json()
        apientries = apidata.get('items', [])

        if apientries:
            snippet = apientries[0].get('snippet', {})
            uploader_name = snippet.get("channelTitle", "")
            content_details = apientries[0].get('contentDetails', {})
            region_restriction = content_details.get('regionRestriction', {})
            
            if uploader_name.lower() == f"{channel_name}":
                available_videos[video_id] = {"title": title, "duration": duration}
                continue

            if "blocked" in region_restriction and "IE" in region_restriction["blocked"]:
                with open(unavailable_files, "a") as f:
                    f.writelines(f"{video_id}, {title}\n")
                continue

            available_videos[video_id] = {"title": title, "duration": duration}
        else:
            # deleted_entries.append(entry)
            with open(deleted_files, "a") as f:
                f.write(f"ID: {entry['id']}, Title: {entry['title']}\n")

    return available_videos

# This entire function is just to make sure that I won't be overwriting ANY files with the same name.
def check_titles(available_videos, output_file="duplicates.txt"):
    title_dict = {}
    output_data = []
    duplicates_found = False

    for video_id, entry in available_videos.items():
        title = entry['title']

        if title in title_dict:
            duplicates_found = True

            if title_dict[title]['count'] == 1:
                if {title_dict[title]['video_id']} == video_id:
                    continue

                output_data.append(f"ORIGINAL - Video ID: {title_dict[title]['video_id']}, Title: {title}\n")

            output_data.append(f"DUPLICATE - Video ID: {video_id}, Title: {title}\n\n")
            
            title_dict[title]['count'] += 1

        else:
            title_dict[title] = {'video_id': video_id, 'count': 1}

    if output_data:
        with open(output_file, "a") as f:
            f.writelines(output_data)

    if duplicates_found:
        raise DuplicateTitle("Video title duplicate, cancelling process.")

# Makes the .m3u8 file, takes in the processed entries from get_playlist_info
def generate_playlist(directory, playlist_name, ytapi_processed):
    playlist_pathfile = os.path.join(directory, f"{playlist_name}.m3u8")
    file_exists = os.path.exists(playlist_pathfile)
    
    with open(playlist_pathfile, 'a', encoding='utf-8') as f:
        if not file_exists:
            f.write("#EXTM3U\n")
        
        for entry in ytapi_processed:
            title, duration = entry

            f.write(f"#EXTINF:{int(duration)}, {title}\n")
            f.write(f"{title}.opus\n")

# TODO Future proof, check if 2 songs are the same before generating playlist, aka duplicate songs just stacking on each other