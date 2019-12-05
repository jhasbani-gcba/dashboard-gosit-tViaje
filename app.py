from helper import lectura_archivos as rf
from helper import tiempoViaje as tv
from map_helper import map_helper
import plotly.graph_objs as go
import datetime
import dash
import dash_core_components as dcc
import dash_html_components as html
import os
import glob
import pandas as pd
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate


csalles_dir = os.path.abspath('/Users/Joni/Documents/matriz-OD/02_identificacion-archivos/Logs-U4-campos-salles')
pico_dir = os.path.abspath('/Users/Joni/Documents/matriz-OD/02_identificacion-archivos/Logs-U5-pico')
mapbox_access_token = 'pk.eyJ1Ijoiamhhc2JhbmkiLCJhIjoiY2szajQ5azVsMGZhZDNua29vemttNmVqMiJ9.T6WftYf3JpP6OJ3fXfeWCw'
LPR_coord = pd.read_csv('LPR_coordenadas.csv')

if 'TT.csv' not in os.listdir(os.getcwd()):
    dias = [3, 4, 5, 6]

    for i, dia in enumerate(dias):
        csalles_files = glob.glob(csalles_dir + '/*0' + str(dia) + '.log')
        pico_files = glob.glob(pico_dir + '/*0' + str(dia) + '.log')

        print('Definiendo el sentido para el dia {}'.format(dia))
        O, D = rf.get_OD_df(csalles_files, pico_files)
        if i == 0:
            print('Tiempo de viaje para el dia {}'.format(dia))
            TT_df = tv.get_ttravel_df(O, D, 6,1500)
        else:
            print('Tiempo de viaje para el dia {}'.format(dia))
            aux_tt = tv.get_ttravel_df(O, D, 6,1500)
            TT_df = TT_df.append(aux_tt)

    TT_df.to_csv('TT.csv', index=False)
else:
    TT_df = pd.read_csv('TT.csv')

data_plot = [TT_df]


#######################################  APPLICATION ######################################################
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = 'Proyecto GCBA'

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}

app.layout = html.Div([
    html.Div([
        html.Div([
            html.Label("Promedio cada: [min]"),
            dcc.Input(
                        id="input-min",
                        type="number",
                        value=5,
                        placeholder="Tiempo para promedio",
                        debounce=True,
                    ),
        ],style={'width': 'auto','height':'auto','position': 'relative','bottom':'14px','fontSize':'14px','display': 'inline-block','color':colors['text']}),
        html.Div([
            html.Label('Tipo de gráfico'),
            dcc.RadioItems(
                                    id = 'grafico-opt',
                                    options=[
                                        {'label': 'Tiempo de viaje', 'value': 'TT'},
                                        {'label': 'Velocidad', 'value': 'Vel'}
                                    ],
                                    value='TT',
                                    labelStyle={'display': 'inline-block'}
                                )
                    ],style={'width': '35%','height':'auto', 'position': 'relative','left':'20px','fontSize':'14px', 'display': 'inline-block','color':colors['text']})
    ],style = {'position': 'static','margin':'20px 0 0 0', 'width':'30%','height':'auto'}),
    html.Div([
        html.Div([
            dcc.Graph(id='graph-with-input',),
            ],style={'width': '70%','position':'absolute','display': 'inline-block'}),
        html.Div([
            dcc.Store(id='memory'),
            dcc.Graph(id='mapa_LPR')
            ],style = {'width': '30%','position':'relative', 'left':'897px','display': 'inline-block'})
    ],style={'position': 'relative', 'margin': '0', 'top': '50px'}),
],style = {'margin':'0 auto', 'width':'95%','background-color':'#111111','text-color':'#7FDBFF'})

################################## CALLBACKS ########################################

@app.callback(
    Output('graph-with-input', 'figure'),
    [Input('input-min', 'value'),
     Input('grafico-opt','value')])
def update_figure(avg_time,grafico):
    if grafico == 'TT':
        keys = ['T_viaje','T_viaje_avg','T_viaje_poly']
        avg_df = tv.get_avg_df(TT_df, avg_time,metrica = 'Tiempo')
        poly_df = tv.get_poly_df(avg_df,metrica = 'Tiempo')
        ytick_vals = list(range(0, max(TT_df['T_viaje'].values.tolist()), 30))
        ytick_labels = [str(datetime.timedelta(seconds=t)) for t in range(0, max(TT_df['T_viaje'].values.tolist()), 30)]
        y_axis_title = 'Tiempo de viaje [s] <br> </b>'
    else:
        keys = ['Velocidad', 'V_avg', 'V_poly']
        avg_df = tv.get_avg_df(TT_df, avg_time, metrica = 'Velocidad')
        poly_df = tv.get_poly_df(avg_df,metrica = 'Velocidad')
        ytick_vals = list(range(0,70,10))
        ytick_labels = [str(tick) for tick in ytick_vals]
        y_axis_title = 'Velocidad media [Km/h] <br> </b>'

    data_plot = [
        go.Scatter(x=TT_df['Hora'],
                   y=TT_df[keys[0]],
                   mode='markers',
                   marker=dict(color=colors['text'], size=3),
                   text=TT_df['Patente'],
                   name=keys[0]
                   ),
        go.Scatter(x=avg_df['Hora'],
                   y=avg_df[keys[1]],
                   mode='markers',
                   marker=dict(color='yellow',size=5),
                   name='Promedio cada {} min.'.format(avg_time)
                   ),
        go.Scatter(x=poly_df['Hora'],
                   y=poly_df[keys[2]],
                   mode='lines',
                   marker=dict(color='red'),
                   line_width=3,
                   name='Curva de ajuste del promedio'
                   ),
    ]
    return {
            'data': data_plot,
            'layout': {
                'yaxis': {'title': y_axis_title,
                          'tickmode': 'array',
                          'tickvals': ytick_vals,
                          'ticktext': ytick_labels,
                          },
                'yaxis_tickformat': '%M:%S s',
                'xaxis': {'title': 'Fecha y hora'},
                'plot_bgcolor': colors['background'],
                'paper_bgcolor': colors['background'],
                'font': {
                    'color': colors['text']
                },
                'margin': {'r': 0, 't': 0},
                'hovermode':'closest',
                'legend': go.layout.Legend(
                    x=-0.075,
                    y=1.25,
                    traceorder="normal",
                    font=dict(
                        family="sans-serif",
                        size=12,
                        color="black"
                    ),
                    bgcolor="White",
                    bordercolor="Black",
                    borderwidth=1
                )
            }
        }

@app.callback(
    Output('memory','data'),
    [Input('mapa_LPR', 'clickData')],
    [State('memory', 'data')]
)
def on_click(clickData,data):
    if clickData is None:
        raise PreventUpdate

    data = data or {'origen':{},'destino':{}}
    if len(data['origen'])!=0 and len(data['destino'])!=0:
        data = {}

        data['origen'] = {'text': clickData['points'][0]['text'], 'lon': clickData['points'][0]['lon'],'lat': clickData['points'][0]['lat']}
        data['destino']={}

    elif len(data['origen'])==0:
        data['origen']={'text':clickData['points'][0]['text'], 'lon':clickData['points'][0]['lon'],'lat':clickData['points'][0]['lat']}
    elif len(data['origen']) != 0 and len(data['destino']) == 0:
        point = {'text': clickData['points'][0]['text'], 'lon': clickData['points'][0]['lon'],'lat': clickData['points'][0]['lat']}
        if point != data['origen']:
            data['destino'] = point
        else:
            None

    return data

@app.callback(
    Output('mapa_LPR', 'figure'),
    [Input('memory','modified_timestamp')],
    [State('memory', 'data')]
)
def display_route(ts,data):
    if data is None:
        layer = []
        scatter_origen = []
        scatter_destino = []
    else:
        if len(data['origen']) != 0 and len(data['destino']) == 0:
            layer = []
            scatter_origen = go.Scattermapbox(
                lat=[data['origen']['lat']],
                lon=[data['origen']['lon']],
                text=[data['origen']['text']],
                name='Origen',
                mode='markers',
                marker=dict(
                    size=10,
                    color='blue',
                    opacity=.8,
                )
            )
            scatter_destino = []
        elif len(data['origen']) != 0 and len(data['destino']) != 0:
            route = {}
            route['origen_lon'] = data['origen']['lon']
            route['origen_lat'] = data['origen']['lat']
            route['destino_lon'] = data['destino']['lon']
            route['destino_lat'] = data['destino']['lat']

            coordinates = map_helper.mapbox_request(route,mapbox_access_token)
            layer = map_helper.get_layer(coordinates)

            scatter_origen = go.Scattermapbox(
                lat=[data['origen']['lat']],
                lon=[data['origen']['lon']],
                text=[data['origen']['text']],
                name='Origen',
                mode='markers',
                marker=dict(
                    size=10,
                    color='green',
                    opacity=.8,
                ),

                    )
            scatter_destino = go.Scattermapbox(
                lat=[data['destino']['lat']],
                lon=[data['destino']['lon']],
                text=[data['destino']['text']],
                mode='markers',
                name='Destino',
                marker=dict(
                    size=10,
                    color='green',
                    opacity=.8,
                ),

            )


    # set the geo=spatial data
    data_scattermapbox = [go.Scattermapbox(
                            lat=LPR_coord['Latitud'],
                            lon=LPR_coord['Longitud'],
                            text=LPR_coord['Interseccion'],
                            mode='markers',
                            name='LPR',
                            marker=dict(
                                size=8,
                                color='fuchsia',
                                opacity=.8,
                            ),
                        ),
    ]
    if scatter_origen != [] and scatter_destino == []:
        data_scattermapbox.append(scatter_origen)
    if scatter_origen != [] and scatter_destino != []:
        data_scattermapbox.append(scatter_origen)
        data_scattermapbox.append(scatter_destino)


    # set the layout to plot
    layout = go.Layout(autosize=True,
                       mapbox=dict(accesstoken=mapbox_access_token,
                                   layers=layer,
                                   bearing=0,
                                   pitch=0,
                                   zoom=11,
                                   center=dict(lat=-34.60,
                                               lon=-58.43),
                                   style='dark'),
                       width=385,
                       height=450,
                       margin = {'l': 0, 'r': 0, 't': 0, 'b': 0},
                       showlegend=False,
                       hoverlabel_align='right',
                       hovermode='closest',
                       clickmode='event+select')

    fig = dict(data=data_scattermapbox, layout=layout)
    return fig

if __name__ == '__main__':
    app.run_server(host='10.78.163.85', port=5000, debug=True)


