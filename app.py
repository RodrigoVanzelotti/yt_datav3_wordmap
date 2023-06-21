import dash
import dash_bootstrap_components as dbc

app = dash.Dash(external_stylesheets=[dbc.themes.CYBORG, dbc.icons.FONT_AWESOME])

app.config['suppress_callback_exceptions'] = True
app.scripts.config.serve_locally = True
server = app.server