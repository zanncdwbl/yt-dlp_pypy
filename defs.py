import os, re, subprocess, json, requests, pickle
from google_auth_oauthlib.flow import InstalledAppFlow
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

def change_duration_to_int(duration):
    # print(f"Duration: {duration}")

    pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
    match = pattern.match(duration)

    hours = match.group(1) if match.group(1) else None
    minutes = match.group(2) if match.group(2) else None
    seconds = match.group(3) if match.group(3) else None

    total_seconds = 0
    if hours:
        total_seconds += int(hours) * 3600
    if minutes:
        total_seconds += int(minutes) * 60
    if seconds:
        total_seconds += int(seconds)
    
    return total_seconds

# Command line instead of python, gets all of the video metadata, 
def yt_flat_playlist(playlist_url, playlist_name):
    print(f"\nProcessing playlist: {playlist_name}\n\n")
    # changed to only get ids, since it gets unavailable videos
    command = f"yt-dlp -no-warnings -i --flat-playlist --print %(id)s -I ::-1 {playlist_url}"
    result = subprocess.run(command, text=True, shell=True, capture_output=True, check=True, errors='ignore')

    archive_ids = []
    video_ids = []

    try:
        with open(archive, "r") as archive:
            for line in archive:
                existing_ids = line.strip().replace("youtube ", "")
                archive_ids.append(existing_ids)
    except:
        print("No playlist archive found.")
        pass

    for x in result.stdout.strip().splitlines():
        if x not in archive_ids:
            video_ids.append(x)

    print(f"Total video IDs collected: {len(video_ids)}\n")

    return video_ids

SCOPES = ["https://www.googleapis.com/auth/youtube"]
CREDENTIALS_FILE = "token.pickle"

def authenticate_with_oauth():
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "rb") as token:
            credentials = pickle.load(token)
    else:
        flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
        credentials = flow.run_local_server(port=0)

        with open(CREDENTIALS_FILE, "wb") as token:
            pickle.dump(credentials, token)

    return credentials

# Takes video ids and does some checks to send to deleted or unavailable files, and returns other available videos
def get_playlist_info(playlist_name, headers, video_ids = []):
    print("Checking for Unavailable videos.")

    unavailable_file = f"unavailableSongs_{playlist_name}.txt"
    deleted_file = f"deletedSongs_{playlist_name}.txt"

    valid_api_ids = []

    available_videos = {}
    deleted_ids = []

    # #start, end, step
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        video_ids_string = ",".join(batch)

        response = requests.get(f'https://www.googleapis.com/youtube/v3/videos?id={video_ids_string}&part=contentDetails,snippet', headers=headers).json()
        # response = requests.get(BASE_URL, params=params).json()

        items = response.get("items", [])

        for api_video_entry in items:
            valid_api_ids.append(api_video_entry.get("id")) #add ids which were returned with the api call, means they are valid anyway

            snippet = api_video_entry.get("snippet")
            video_title = snippet.get("title")
            uploader_name = snippet.get("channelTitle")

            content_details = api_video_entry.get("contentDetails")
            # print(api_video_entry.get("id"))
            video_duration = change_duration_to_int(content_details.get("duration"))
            region_restriction = content_details.get("regionRestriction")

            if uploader_name == channel_name:
                available_videos[api_video_entry.get("id")] = {"title": video_title, "duration": video_duration}
                continue

            if region_restriction and isinstance(region_restriction, dict):
                if "blocked" in region_restriction and "IE" in region_restriction["blocked"]:
                    with open(unavailable_file, "a") as f:
                        f.write(f"ID: {api_video_entry.get('id')}, Title: {video_title}\n")
                    continue

            available_videos[api_video_entry.get("id")] = {"title": video_title, "duration": video_duration}

    for video_id in video_ids:
        if video_id not in valid_api_ids:
            with open(deleted_file, "a") as f:
                deleted_ids.append(video_id)
                f.write(f"ID: {video_id}\n")

    return available_videos, deleted_ids

# This entire function is just to make sure that I won't be overwriting ANY files with the same name.
def check_titles(playlist_name, available_videos = []):
    print("Checking videos for duplicate titles.")
    output_file=f"duplicatesFound_{playlist_name}.txt"

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
        raise DuplicateTitle(f"Duplicate title(s) found in playlist '{playlist_name}'")
    else:
        print("No duplicates found.\n")

# # Makes the .m3u8 file, takes in the processed entries from get_playlist_info
def generate_playlist(directory, playlist_name, available_videos = [], video_ids = []):
    if not os.path.exists(directory):
        os.makedirs(directory)
    playlist_pathfile = os.path.join(directory, f"{playlist_name}.m3u8")
    file_exists = os.path.exists(playlist_pathfile)

    with open(playlist_pathfile, 'a', encoding='utf-8') as f:
        if not file_exists:
            f.write("#EXTM3U\n")
        
        for id, entry in available_videos.items():
            title = entry["title"]
            duration = entry["duration"]

            if id in video_ids:
                f.write(f"#EXTINF:{int(duration)}, {title}\n")
                f.write(f"{title}.opus\n")

def delete_deletedVidoes(playlist_url, headers, deleted_ids = []):
    print("Deleting private and/or deleted videos from playlist.")

    playlist_id = playlist_url.strip().replace("https://www.youtube.com/playlist?list=", "")
    # print(playlist_id)

    BASE_URL = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        "part": "snippet",
        "playlistId": playlist_id,
        "fields": "items(id,snippet.resourceId.videoId),nextPageToken",
        "maxResults": 50,
        # "key": api_key
    }

    to_delete_ids = []
    nextpage = None

    while True:
        if nextpage:
            params["pageToken"] = nextpage

        response = requests.get(BASE_URL, params=params, headers=headers).json()

        for item in response.get("items", []):
            snippet = item.get("snippet")
            resource_id = snippet.get("resourceId")
            short_id = resource_id.get("videoId")

            if short_id in deleted_ids:
                print(short_id)
                to_delete_ids.append(item.get("id"))

        nextpage = response.get("nextPageToken")
        if not nextpage:
            break

    if to_delete_ids:
        print(len(to_delete_ids))
        for longID in to_delete_ids: 
            # print(f"Deleting {video_ids_string} from playlist.")
            response = requests.delete(f'https://www.googleapis.com/youtube/v3/playlistItems?id={longID}', headers=headers)