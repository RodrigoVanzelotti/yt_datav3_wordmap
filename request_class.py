import os
import json
import pandas as pd
from venv import create
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

from typing import Sequence

# Caso queira testar alguns queries, existe a função _test_queries, que contém 3 testes pré setados
# Se acostume a usar a função execute_api_query(**kwargs) para utilizar a classe
# typedefs - NOTE remover?
file_path = str


class ytAnalytics:
    '''SCOPES 
    MANAGE: Gerenciar sua conta do YouTube
    READONLY: Visualize sua conta do YouTube
    PARTNER: Visualize e gerencie seus ativos e conteúdo associado no YouTube
    MONETARY: Visualize relatórios monetários e não monetários do YouTube Analytics para seu conteúdo do YouTube
    ANALYTICS READONLY:Visualize relatórios do YouTube Analytics para seu conteúdo do YouTube
    '''
    ANALYTICS_DATA = {
        'scope': {
            "manage": "https://www.googleapis.com/auth/youtube", 
            "readonly": "https://www.googleapis.com/auth/youtube.readonly", 
            "partner": "https://www.googleapis.com/auth/youtubepartner", 
            "monetary": "https://www.googleapis.com/auth/yt-analytics-monetary.readonly", 
            "analytics_readonly": "https://www.googleapis.com/auth/yt-analytics.readonly"   
        },
        'api_version': 'v2',
        'api_service_name': 'youtubeAnalytics' 
    }

    DATAV3_DATA = {
        'scope': [
            "https://www.googleapis.com/auth/youtube",
            "https://www.googleapis.com/auth/youtube.force-ssl",
            "https://www.googleapis.com/auth/youtube.readonly",
            "https://www.googleapis.com/auth/youtubepartner"],
        'api_version': 'v3',
        'api_service_name': 'youtube'
    }

    # Usado para overlaping de dicionário, em test queries
    TEST_QUERY_DATA = {
        'ids':'channel==MINE',
        'startDate':'2023-01-01',
        'endDate':'2023-04-30',
        'metrics':'estimatedMinutesWatched,views,likes,subscribersGained',
        'dimensions':'day',
        'sort':'day'
    }

    def __init__(self, 
                 scope: Sequence[str]='analytics_readonly',
                 client_secrets_file: file_path='credentials_yt.json',
                 test_env: bool=True):
        
        self.__check_secrets_path(client_secrets_file)
        # self.__check_defined_scope(scope)

        self.client_secrets_file = client_secrets_file
        self.test_env = test_env

        self.scope = self.DATAV3_DATA['scope'] + [self.ANALYTICS_DATA['scope'][scope]]

        flow = InstalledAppFlow.from_client_secrets_file(self.client_secrets_file, self.scope)
        self.server_credentials = flow.run_local_server()

        # Principais objetos de consulta
        # Utilizar o analytics para dados gerais e o datav3 para consultas individuais de vídeo
        self.suppliant_analytics = self.__create_main_request_object("analytics")
        self.suppliant_datav3 = self.__create_main_request_object("datav3")

        '''TEST ENVIRONMENT
        Você deve observar que o Oauth2 funciona por meio da camada SSL. A maioria das pessoas não define o SSL em seu servidor durante o teste e tudo bem.
        Se seu servidor não estiver parametrizado para permitir HTTPS, o método fetch_token gerará um oauthlib.oauth2.rfc6749.errors.InsecureTransportError. 
        '''
        if test_env:
            os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    def execute_api_query(self, **kwargs) -> dict:
        '''
        Realiza a query mais 'crua' do analytics, deve fornecer todos os args

        Returns:
            Dict Data from endpoint
        '''
        response = self.suppliant_analytics.reports().query(
            **kwargs
        ).execute()

        return response

    def get_video_data(self, video_ids:str | list, compact_return:bool = False) -> dict: 
        '''
        Faz o api request por um ou mais ids de vídeo
        
        Returns:
            Response Data from Endpoint, such as:
                - publishedAt
                - title
                - thumbnails
                - viewCount
                - likeCount
                - dislikeCount
                - commentCount
        '''
        if type(video_ids) == list:
            video_ids = ','.join(video_ids)

        response_dict = {}
            
        response = self.suppliant_datav3.videos().list(
            part="snippet, statistics",
            id=video_ids,
        ).execute()

        if not compact_return: 
            response_dict['response'] = response
        else:
            compact_videos = []
            for video in response['items']:
                compact_response = {
                    'title': video['snippet']['title'],
                    'publishedAt': video['snippet']['publishedAt'],
                    'thumbnail_url': video['snippet']['thumbnails']['high']['url'],
                    'viewCount': video['statistics']['viewCount'],
                    'likeCount': video['statistics']['likeCount'],
                    'dislikeCount': video['statistics']['dislikeCount'],
                    'commentCount': video['statistics']['commentCount']
                }
                compact_videos.append(compact_response)
            response_dict['response'] = compact_videos

        return response_dict

    def get_playlist_data(self, playlist_id:str) -> dict:
        # A gente ainda não trabalha com playlist, então ignorar por hora.
        # NOTE função a fazer
        return {}

    def get_channel_stats(self, channel_id:str = 'UCxXL5491Db9U8Rhfs-2LVFg', part:str = 'statistics, brandingSettings', compact_return:bool = False) -> dict:
        '''
        Faz o api request por stats de um canal específico (pré settado como Asimov Academy)
        
        Returns:
            Response Data from Endpoint, such as:
                - title
                - country
                - id
                - viewCount
                - subscriberCount
                - hiddenSubscriberCount
                - videoCount
        '''
        response = self.suppliant_datav3.channels().list(part=part, id=channel_id, maxResults=50).execute()
        if not compact_return: return response
        else:
            base = response['items'][0]
            compact_response = {
                'title': base['brandingSettings']['channel']['title'],
                'country': base['brandingSettings']['channel']['country'],
                'id': base['id'],
                'viewCount': base['statistics']['viewCount'],
                'subscriberCount': base['statistics']['subscriberCount'],
                'hiddenSubscriberCount': base['statistics']['hiddenSubscriberCount'],
                'videoCount': base['statistics']['videoCount']
            }
            return compact_response

    def get_channel_videos(self, channel_id:str = 'UCxXL5491Db9U8Rhfs-2LVFg', compact_return:bool = False) -> dict:
        videos = []
        upload_id = "UU" + channel_id[2:]
        
        request = self.suppliant_datav3.playlistItems().list(
            part="snippet", playlistId=upload_id, maxResults=50)

        response = request.execute()
        responseItems = response['items']
        videos.extend(responseItems)

        # if there is nextPageToken, then keep calling the API
        while response.get('nextPageToken', None):
            request = self.suppliant_datav3.playlistItems().list(
                part="snippet", 
                playlistId=upload_id, 
                pageToken=response['nextPageToken'],
                maxResults=50)
            
            response = request.execute()
            responseItems = response['items']
            videos.extend(responseItems)
        
        print(f"Finished fetching videos for {channel_id}. {len(videos)} videos found.")
        
        if not compact_return:
            return videos
        else:
            compact_videos = []
            for vid in videos:
                compact_videos.append(self.__compact_video_response(vid))
            return compact_videos
        
    def get_top10_videos(self, startDate: str, endDate: str):
        args = {
            'ids':'channel==MINE',
            'dimensions': 'video',
            'metrics': 'estimatedMinutesWatched,views,likes,subscribersGained',
            'startDate': startDate,
            'endDate': endDate,
            'maxResults': 10,
            'sort': '-estimatedMinutesWatched'
        }
        return self.execute_api_query(**args)

    def temporal_data_to_df(self, data: dict) -> pd.DataFrame:
        cols = [col['name'] for col in data['columnHeaders']]
        rows = data['rows']

        return pd.DataFrame(columns=cols, data=rows)

    '''
    Classe criada para testar o retorno de queries simples, foram criadas 3 queries básicas para teste
    e análise de dados.
    0. Contagens de visualizações específicas do país (e mais) para um canal
    1. Top 10 – Vídeos mais assistidos de um canal
    2. Top 10 – Playlists mais assistidas para um canal
    '''
    def _test_queries(self, test_value: int=0):
        '''
        Faz Query Tests já pré estabelecidos, utilizado para debugar o código e salvar possibilidades

        Returns:
            Response Data from Endpoint
        '''
        query_dict = self.TEST_QUERY_DATA.copy()

        match test_value:
            case 0:
                return_type = 'Contagens de visualizações específicas do país (e mais) para um canal'
                args = {
                    'metrics': 'views,comments,likes,dislikes,estimatedMinutesWatched',
                    'filters': 'country==BR'
                }
            case 1:
                return_type = 'Top 10 – Vídeos mais assistidos de um canal'
                args = {
                    'dimensions': 'video',
                    'metrics': 'estimatedMinutesWatched,views,likes,subscribersGained',
                    'maxResults': 10,
                    'sort': '-estimatedMinutesWatched'
                }
            case 2:
                return_type = 'Top 10 – Playlists mais assistidas para um canal'
                args = {        
                    'dimensions': 'playlist',
                    'metrics': 'estimatedMinutesWatched,views,playlistStarts,averageTimeInPlaylist',
                    'filters': 'isCurated==1',
                    'maxResults': 10,
                    'sort': '-estimatedMinutesWatched'
                }

        query_dict.update(args)    
        print(f'\n\tSample Request ====================\nTipo: {return_type}\nArgumentos = {query_dict}')
        return self.execute_api_query(**query_dict)
    
    def __create_main_request_object(self, api_type:str) -> object:
        if api_type == "analytics":
            api_version = self.ANALYTICS_DATA['api_version']
            api_service_name = self.ANALYTICS_DATA['api_service_name']
        elif api_type == "datav3":
            api_version = self.DATAV3_DATA['api_version']
            api_service_name = self.DATAV3_DATA['api_service_name']            
        else:
            raise ValueError(f"Valor de Type '{api_type}' Inválido. O valor deve ser analytics | datav3")
        
        return build(api_service_name, api_version, credentials=self.server_credentials)

    @staticmethod
    def __check_secrets_path(path: str) -> None:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Não foi possível criar a Classe ytAnalytics. Arquivo não encontrado: \n\t{path}")
        else: return

    @staticmethod
    def __check_defined_scope(self, defined_scope: str) -> None:
        if self.ANALYTICS_DATA['scope'].get(defined_scope) is None:
            raise ValueError(f"O escopo definido na criação '{defined_scope}' da Classe não é válido.\nEscopos Válidos: manage | readonly | partner | monetary | analytics_readonly")
        else: return
    
    @staticmethod
    def __compact_video_response(video_dict: dict) -> dict:
        compact_video_dict = {
            'title': video_dict['snippet']['title'],
            'id': video_dict['id'],
            'publishedAt': video_dict['snippet']['publishedAt'],
            'thumbnails': video_dict['snippet']['thumbnails']
        }
        return compact_video_dict
    
if __name__ == "__main__":
    def save_sample(ret, filename):
        ret = json.dumps(ret, indent=4)
        json_path = os.path.join('Data_Consumption', 'Youtube', 'Sample_Requests', filename)
        with open(json_path, 'w') as f:
            f.write(ret)

    def read_sample(filename):
        json_path = os.path.join('Data_Consumption', 'Youtube', 'Sample_Requests', filename)
        with open(json_path, 'r') as f:
            data = json.load(f)
        return data

    object = ytAnalytics()

    retorno = object._test_queries(0)
    save_sample(retorno, 'sample_azar.json')
    # print(retorno)

    # print()

    # retorno = object.get_video_data('P6M9dK0T_Nk', True)
    # save_sample(retorno, 'video_sample_request.json')

    # retorno = object.get_channel_stats(compact_return=True)
    # save_sample(retorno, 'compact_channel_stats_sample.json')

    # retorno = object.get_channel_videos(compact_return=True)
    # save_sample(retorno, 'compact_channel_videos_sample.json')

    # retorno = object.get_top10_videos('2023-01-01', '2023-05-28')
    # save_sample(retorno, 'top10_videos_sample.json')

    # data = read_sample('top10_videos_sample.json')
    # columns = []
    # for data_column in data['columnHeaders']:
    #     columns.append(data_column['name'])

    # df = pd.DataFrame(data=data['rows'], columns=columns)
    # video_list = df['video'].tolist()

    # video_data = object.get_video_data(video_list, False)
    # save_sample(video_data, 'top10_videos_specific_sample_from_id.json')


    # object.get_playlist_data('PLuvoZvhxWzZBAPVgpyK-nxjaev718o6UJ')
