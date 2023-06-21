import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, dcc, html, no_update

import stylecloud
from request_class import ytAnalytics

from app import *

youtube = ytAnalytics()

# STYLE =====================
CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

# LAYOUT ====================
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.Legend('WordCloud - Youtube'),
            html.Hr(),
        ])
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Input(id="input_text", placeholder="Type your search term...", type="text"),
        ]),
        dbc.Col([
            dbc.Button('Search', id='search_button')
        ], md=1, align='end')
    ]),
    dbc.Row([
        dbc.Col([
            html.Img(id='wordcloud_image')     
        ])
    ])

],id='page_content')


# CALLBACKS =================
@app.callback(
    Output('wordcloud_image', 'src'),
    Input('search_button', 'n_clicks'),
    State('input_text', 'value')
)
def update_wordcloud(n, input_txt):
    if (n is None) or (input_txt is None):
        return no_update
    else:
        print(input_txt)
        return None

# SERVER ====================
if __name__ == "__main__":
    app.run_server(port=8051, debug=True)