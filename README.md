TODO / What it should do\

Download main playlist, as per normal with ytdlp\
open file (if exists)> save all titles in a hashmap > check if title repeats itself (since files overwrite) > save into file - print out > same for deleted.


Youtube API call to check if video is available (region locked etc)\
https://www.googleapis.com/youtube/v3/videos?id=&part=status,contentDetails&key=\
But I also could, get all the NON downloaded video's from main and then just add to list, ID or Title - this would only work for a massive playlist download

Alt Playlists > Flat download\
Get title, replace special characters > Append duration, title to m3u8 playlist > If video is unavailable (per api call or ID check, dont append to playlist)

Remove thumbnail that gets downloaded\

Update ReadME

make the api call adhere to the archive.
api call batch request for video ids