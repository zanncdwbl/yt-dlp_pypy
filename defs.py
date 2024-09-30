import os, re, subprocess, json, requests
from vars import *

class DuplicateTitle(Exception):
    pass

# Used to make sure that even when we use flatplaylist, it will return how the actual downloaded songs are.
def replace_special_characters(title):
    title = re.sub(r'\|', '｜', title)
    title = re.sub(r'"', '＂', title)
    title = re.sub(r'\?', '？', title)
    title = re.sub(r'/', '⧸', title)
    title = re.sub(r'\*', '＊', title)
    title = re.sub(r':', '：', title)
    return title

# Command line instead of python, gets all of the video metadata, sends it into file, which is processed to get entry info in playlist
def get_playlist_info(playlist_url, output_file = "output.txt", deleted_files = "deleted.txt"):
    command = f'yt-dlp --flat-playlist --dump-single-json -I ::-1 "{playlist_url}" | jq . > {output_file}'

    subprocess.run(command, text=True, shell=True, check=True)

    with open(output_file, 'r', encoding='utf-8') as file:
        data = json.load(file)

    entries = data.get('entries', [])

    processed_entries = []
    deleted_entries = []
    for entry in entries:
        title = entry.get('title')
        title = replace_special_characters(title)

        if any(term.lower() in title.lower() for term in ["deleted", "unavailable", "private"]):
            deleted_entry = {
                'id': entry.get('id'),
                'title': title,
                'duration': entry.get('duration', 0)
            }
            deleted_entries.append(deleted_entry)
            continue

        processed_entry = {
            'id': entry.get('id'),
            'title': title,
            'duration': entry.get('duration', 0)
        }
        processed_entries.append(processed_entry)

    # os.remove(output_file)

    with open(deleted_files, "a") as f:
        for entry in deleted_entries:
            f.write(f"ID: {entry['id']}, Title: {entry['title']}\n")

    return processed_entries

def check_titles(processed_entries, output_file="duplicates.txt"):
    title_dict = {}
    duplicates_found = False
    output_data = []

    for entry in processed_entries:
        video_id = entry['id']
        title = entry['title']

        # Hashmap to check for duplicate titles, basically it adds all titles to a file, then if ever theres a second title with same name it will write that its dupe
        if title in title_dict:
            title_dict[title] += 1
        else:
            title_dict[title] = 1

        if title_dict[title] == 1:
            unique_title = title
        else:
            unique_title = f"{title} (Duplicate {title_dict[title]})"
        output_data.append(f"Video ID: {video_id}, Title: {unique_title}\n")

        if title_dict[title] > 1:
            duplicates_found = True

    with open(output_file, "a") as f:
        f.writelines(output_data)

    if duplicates_found:
        raise DuplicateTitle("Video title duplicate, cancelling process.")

def yt_apicall(processed_entries, output_file="blocked.txt"):
    ytapi_processed = []

    for entry in processed_entries:
        video_id = entry['id']
        video_title = entry['title']
        duration = entry['duration']

        #removed status cause its not really needed if we already parse deleted/private etc in flat
        req = requests.get(f'https://www.googleapis.com/youtube/v3/videos?id={video_id}&part=contentDetails&key={api_key}')
        entries = req.get('items', [])

        if entries:
            content_details = entries[0].get('contentDetails', {})
            region_restriction = content_details.get('regionRestriction', {})

            if 'blocked' in region_restriction and 'IE' in region_restriction['blocked']:
                with open(output_file, "a") as f:
                    f.writelines(f"{video_id}, {video_title}\n")
                continue
            ytapi_processed.append((video_id, video_title, duration))

        return ytapi_processed

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

# TODO Future proof, check if 2 songs are the same before generating playlist