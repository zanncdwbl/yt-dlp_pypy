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

# Command line instead of python, gets all of the video metadata, sends it into file, which is processed to get entry info in playlist
def get_playlist_info(playlist_url, unavailable_files = "unavailable.txt", deleted_files = "deleted.txt"):
    print("Fetching playlist data...")
    # changed to only get ids, since it gets unavailable videos
    command = f"yt-dlp -no-warnings -i --flat-playlist --print %(id)s -I ::-1 {playlist_url}"
    result = subprocess.run(command, text=True, shell=True, capture_output=True, check=True, errors='ignore')

    archive_ids = []
    video_ids = []
    valid_api_ids = []
    api_responses = []
    available_videos = {}

    with open(".mainarchive.txt", "r") as archive:
        for line in archive:
            existing_ids = line.strip().replace("youtube ", "")
            archive_ids.append(existing_ids)

    for x in result.stdout.strip().splitlines():
        if x not in archive_ids:
            video_ids.append(x)

        # video_ids.append(x)

    print(f"Total video IDs collected: {len(video_ids)}")

    # #start, end, step
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        video_ids_string = ",".join(batch)

        req = requests.get(f'https://www.googleapis.com/youtube/v3/videos?id={video_ids_string}&part=contentDetails,snippet&key={api_key}')
        req.raise_for_status()

        apidata = req.json()
        api_responses.append(apidata)

    for api_response in api_responses:
        apientries = api_response.get('items', [])

        for api_video_entry in apientries:
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
                    with open(unavailable_files, "a") as f:
                        f.write(f"ID: {api_video_entry.get('id')}, Title: {video_title}\n")
                    continue

            available_videos[api_video_entry.get("id")] = {"title": video_title, "duration": video_duration}

    for video_id in video_ids:
        if video_id not in valid_api_ids:
            with open(deleted_files, "a") as f:
                f.write(f"ID: {video_id}\n")

    print("Completed processing.")
    return available_videos

# This entire function is just to make sure that I won't be overwriting ANY files with the same name.
# def check_titles(available_videos, output_file="duplicates.txt"):
#     title_dict = {}
#     output_data = []
#     duplicates_found = False

#     for video_id, entry in available_videos.items():
#         title = entry['title']

#         if title in title_dict:
#             duplicates_found = True

#             if title_dict[title]['count'] == 1:
#                 if {title_dict[title]['video_id']} == video_id:
#                     continue

#                 output_data.append(f"ORIGINAL - Video ID: {title_dict[title]['video_id']}, Title: {title}\n")

#             output_data.append(f"DUPLICATE - Video ID: {video_id}, Title: {title}\n\n")
            
#             title_dict[title]['count'] += 1

#         else:
#             title_dict[title] = {'video_id': video_id, 'count': 1}

#     if output_data:
#         with open(output_file, "a") as f:
#             f.writelines(output_data)

#     if duplicates_found:
#         raise DuplicateTitle("Video title duplicate, cancelling process.")

# # Makes the .m3u8 file, takes in the processed entries from get_playlist_info
# def generate_playlist(directory, playlist_name, ytapi_processed):
#     playlist_pathfile = os.path.join(directory, f"{playlist_name}.m3u8")
#     file_exists = os.path.exists(playlist_pathfile)
    
#     with open(playlist_pathfile, 'a', encoding='utf-8') as f:
#         if not file_exists:
#             f.write("#EXTM3U\n")
        
#         for entry in ytapi_processed:
#             title, duration = entry

#             f.write(f"#EXTINF:{int(duration)}, {title}\n")
#             f.write(f"{title}.opus\n")