import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, dcc, html, no_update

import stylecloud
from request_class import ytAnalytics
from word_counter import count_word_occurrences

from app import *

global youtube

# STYLE =====================
CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "margin-top": "2rem",
    "padding": "2rem 1rem",
}

# LAYOUT ====================
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.Legend('WordCloud - Youtube'),
        ]),
        dbc.Col([
            dbc.Button('Youtube Login', id='login_button', color='primary', style={'margin': '0px 0px 8px'})
        ], md=2, align='end'),
        html.Hr()
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Input(id="input_text", placeholder="You must login to youtube before searching...", type="text"),
        ]),
        dbc.Col([
            dbc.Button('Search', id='search_button', color='secondary', disabled=True)
        ], md=1, align='end')
    ]),
    dbc.Row([
        dbc.Col([
            # html.Legend('Top 5 Palavras'),
            html.P(id='resultados')
        ])
    ]),
    dbc.Row([
        dbc.Col([
            html.Img(id='wordcloud_image', src=app.get_asset_url('wordcloud.png'))     
        ])
    ],justify="center", style={'textAlign': 'center'})

],id='page_content', style={"margin-top": "1rem"})


# CALLBACKS =================
@app.callback(
    Output('search_button', 'disabled'),
    Output('login_button', 'disabled'),
    Output('search_button', 'color'),
    Output('login_button', 'color'),
    Output('input_text', 'placeholder'),
    Input('login_button', 'n_clicks')
)
def youtube_login(n):
    if n is None:
        return no_update
    else:
        global youtube
        youtube = ytAnalytics()
        return False, True, 'primary', 'secondary', 'Type your search term...'

@app.callback(
    Output('wordcloud_image', 'src'),
    Input('search_button', 'n_clicks'),
    State('input_text', 'value'),
)
def update_wordcloud(n, input_txt):
    if (n is None) or (input_txt is None):
        return no_update
    else:
        global youtube
        output_filename = 'assets/wordcloud.png'

        retorno = youtube.execute_api_query_v3(
                part="snippet",
                channelType="any",
                maxResults=50,
                order="viewCount",
                q=input_txt,
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
                q=input_txt,
                videoType="any"
            )

        for item in retorno['items']:
            title = item['snippet']['title']
            all_titles.append(title)

        all_words = ' '.join(all_titles)

        stylecloud.gen_stylecloud(text=all_words,
                          icon_name='fas fa-apple-alt',
                          palette='cartocolors.qualitative.Pastel_3',
                        #   colors='white',
                          background_color='black',
                          output_name=output_filename,
                          collocations=False)
        
        word_counts = dict(count_word_occurrences(all_words))
        list(word_counts.items())[:5]
        
        return app.get_asset_url(output_filename)



# SERVER ====================
if __name__ == "__main__":
    app.run_server(port=8051, debug=True)