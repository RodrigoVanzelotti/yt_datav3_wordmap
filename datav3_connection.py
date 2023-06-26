from request_class import ytAnalytics
# from sample_handler import save_sample, read_sample
from word_counter import count_word_occurrences 

search_term = 'minecraft'

youtube = ytAnalytics()

retorno = youtube.execute_api_query_v3(
                part="snippet",
                channelType="any",
                maxResults=50,
                order="viewCount",
                q="minecraft",
                videoType="any"
            )

all_titles = []
for item in retorno['items']:
    title = item['snippet']['title']
    all_titles.append(title)

next_page = retorno['nextPageToken']

retorno = youtube.execute_api_query_v3(
                part="snippet",
                pageToken=next_page,
                channelType="any",
                maxResults=50,
                order="viewCount",
                q="minecraft",
                videoType="any"
            )

for item in retorno['items']:
    title = item['snippet']['title']
    all_titles.append(title)

print(len(all_titles))
# save_sample(retorno, 'sample_datav3_minecraft.json')

