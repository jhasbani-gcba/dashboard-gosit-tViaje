from helper import lectura_archivos as rf
from helper import tiempoViaje as tv
from map_helper import map_helper
import plotly.graph_objs as go
import datetime
from datetime import datetime as dt
import dash
import dash_core_components as dcc
import dash_html_components as html
import os
import numpy as np
import pandas as pd
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from cassandra.cluster import Cluster


csalles_dir = os.path.abspath('/Users/Joni/Documents/matriz-OD/02_identificacion-archivos/Logs-U4-campos-salles')
pico_dir = os.path.abspath('/Users/Joni/Documents/matriz-OD/02_identificacion-archivos/Logs-U5-pico')
mapbox_access_token = 'pk.eyJ1Ijoiamhhc2JhbmkiLCJhIjoiY2szajQ5azVsMGZhZDNua29vemttNmVqMiJ9.T6WftYf3JpP6OJ3fXfeWCw'
LPR_coord = pd.read_csv('LPR_coordenadas.csv')


### QUERY PARA OBTENER COORDENADAS DE LAS CAMARAS ###
def connect_cluster():
    cluster = Cluster(contact_points= ['192.168.120.46'], port = 19042)
    session = cluster.connect()
    session.set_keyspace('delivery')

    return [cluster, session]

connection = connect_cluster()
cluster = connection[0]
session = connection[1]
source_query = "SELECT DISTINCT source_id FROM captures"
results = session.execute(source_query, timeout=20.0)
lat = []
lon = []
for row in results:
    r = list(row)[0]
    if r != '0,0' and r != '0.0,0.0':
        coords = r.split(',')
        lat.append(coords[0])
        lon.append(coords[1])

sources = {'lat': lat, 'lon': lon}
sources_df = pd.DataFrame(sources)
sources_df.head()
cluster.shutdown()

#######################################  APPLICATION ######################################################
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = 'Proyecto GCBA'

colors = {
    'background': '#ffffff',
    'text': '#111111'
}
# Layout del dashboard
app.layout = html.Div([
    html.Div(
            className="app-header",
            children=[
                html.Div('Visualización de datos de cámaras de tránsito', className="app-header--title")
            ]
        ),
    html.Div(
            className = 'opciones',
            children=[
                html.H6('Opciones')
    ]),
    # Contenedor de los inputs
    html.Div(
        className='inputs-container',
        children=[
                html.Div(className= 'input-div',
                    children = [
                        html.Div(
                            className= 'input-label',
                            children=[
                            html.Label("Promedio cada: [min]"),
                        ]),
                        html.Div(
                            className= 'input-object',
                            children=[
                                dcc.Input(
                                    id="input-min",
                                    type="number",
                                    value=5,
                                    placeholder="Tiempo para promedio",
                                    debounce=True,
                                ),
                        ])
                ]),
                html.Div(
                    className='input-div',
                    children=[
                        html.Div(
                                className= 'input-label',
                                children=[
                                    html.Label('Tipo de gráfico:')
                        ]),
                        html.Div(
                            className='input-object',
                            children=[
                                dcc.RadioItems(
                                    id='grafico-opt',
                                    options=[
                                        {'label': 'Tiempo de viaje', 'value': 'TT'},
                                        {'label': 'Velocidad', 'value': 'Vel'}
                                    ],
                                    value='TT',
                                    labelStyle={'display': 'inline-block'}
                                )
                        ])
                ]),
                html.Div(
                    className='input-div',
                    children= [
                        html.Div(
                            className='input-label',
                            children=[
                                html.Label('Selección de fecha:')
                        ]),
                        html.Div(
                            className='input-object',
                            children=[
                                 dcc.DatePickerSingle(
                                     id='date-picker',
                                     min_date_allowed=dt(2019, 10, 1),
                                     max_date_allowed=dt.today(),
                                     initial_visible_month=dt(2017, 8, 5),
                                     date=str(dt.strftime(dt.today(), '%Y-%m-%d'))
                                 )
                        ])
                ])
    ]),
    html.Div(
        className='figure-container',
        children=[
            html.Div(
                className= 'plot',
                children=[
                            dcc.Graph(id='graph-with-input',),
            ]),
            html.Div(
                className= 'map',
                children= [
                    dcc.Store(id='memory'),
                    dcc.Graph(id='mapa_LPR')
            ])
    ])
])

################################## CALLBACKS ########################################

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

        data['origen'] = {'lon': clickData['points'][0]['lon'],'lat': clickData['points'][0]['lat']}
        data['destino']={}

    elif len(data['origen'])==0:
        data['origen']={'lon':clickData['points'][0]['lon'],'lat':clickData['points'][0]['lat']}
    elif len(data['origen']) != 0 and len(data['destino']) == 0:
        point = {'lon': clickData['points'][0]['lon'],'lat': clickData['points'][0]['lat']}
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

            request_data = map_helper.mapbox_request(route,mapbox_access_token)
            layer = map_helper.get_layer(request_data[0])

            scatter_origen = go.Scattermapbox(
                lat=[data['origen']['lat']],
                lon=[data['origen']['lon']],
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
                            lat=sources_df['lat'],
                            lon=sources_df['lon'],
                            mode='markers',
                            name='Camaras',
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
                                   style='open-street-map'),
                       width=385,
                       height=450,
                       margin = {'l': 0, 'r': 0, 't': 0, 'b': 0},
                       showlegend=False,
                       hoverlabel_align='right',
                       hovermode='closest',
                       clickmode='event+select')

    fig = dict(data=data_scattermapbox, layout=layout)
    return fig


@app.callback(
    Output('graph-with-input', 'figure'),
    [
        Input('input-min', 'value'),
        Input('grafico-opt', 'value'),
        Input('date-picker', 'date')
    ],
    [State('memory', 'data')]

)
def update_figure(avg_time, grafico, date, data):
    if data is None or len(data) < 2:
        raise PreventUpdate

    if date is not None:
        date = dt.strptime(date.split(' ')[0], '%Y-%m-%d')
        date = dt.strftime(date, '%Y-%m-%d')
    else:
        raise PreventUpdate

    origen_lat = data['origen']['lat']
    origen_lon = data['origen']['lon']
    destino_lat = data['destino']['lat']
    destino_lon = data['destino']['lon']

    route = {}
    route['origen_lon'] = origen_lon
    route['origen_lat'] = origen_lat
    route['destino_lon'] = destino_lon
    route['destino_lat'] = destino_lat

    origen_source = str(origen_lat)+','+str(origen_lon)
    destino_source = str(destino_lat) + ',' + str(destino_lon)

    connection_callback = connect_cluster()
    cluster_callback = connection_callback[0]
    session_callback = connection_callback[1]


    q_origen = rf.make_query(origen_source, date)
    print('Query Origen...')
    results_origen = session_callback.execute(q_origen, timeout=30.0)
    print('Fin query.')
    fechas_df = []
    patentes_df = []
    for row_origen in results_origen:
        r_o = list(row_origen)
        captura = str(rf.utc_to_local(r_o[0]).strftime("%Y-%m-%d %H:%M:%S")).split(' ')
        fecha = captura[0] + 'T' + captura[1]
        fechas_df.append(fecha)
        patentes_df.append(r_o[1])
    cluster_callback.shutdown()

    data_df = list(zip(patentes_df, fechas_df))
    df_origen = pd.DataFrame(data_df, columns=['Patente', 'Fecha']).sort_values(by=['Fecha'])
    df_origen.drop_duplicates(subset='Fecha', keep='first', inplace=True)

    connection_callback = connect_cluster()
    cluster_callback = connection_callback[0]
    session_callback = connection_callback[1]
    print('Query destino...')
    q_destino = rf.make_query(destino_source, date)
    results_destino = session_callback.execute(q_destino, timeout=30.0)
    print('Fin query.')
    fechas_df = []
    patentes_df = []
    for row in results_destino:
        r = list(row)
        captura = str(rf.utc_to_local(r[0]).strftime("%Y-%m-%d %H:%M:%S")).split(' ')
        fecha = captura[0] + 'T' + captura[1]
        fechas_df.append(fecha)
        patentes_df.append(r[1])
    cluster_callback.shutdown()
    data_df = list(zip(patentes_df, fechas_df))
    df_destino = pd.DataFrame(data_df, columns=['Patente', 'Fecha']).sort_values(by=['Fecha'])
    df_destino.drop_duplicates(subset='Fecha', keep='first', inplace=True)
    print('Dataframe armado.')

    request_data = map_helper.mapbox_request(route, mapbox_access_token)
    print(np.ceil(request_data[1] / 60))
    df_origen = rf.filtrar_patentes(df_origen, int(np.ceil(request_data[1]/60)))
    df_destino = rf.filtrar_patentes(df_destino,int(np.ceil(request_data[1]/60)))

    TT_df = tv.get_ttravel_df(df_origen, df_destino, int(np.ceil(request_data[1]/60)), request_data[2])

    if grafico == 'TT':
        keys = ['T_viaje', 'T_viaje_avg', 'T_viaje_poly']
        avg_df = tv.get_avg_df(TT_df, avg_time, metrica='Tiempo')
        poly_df = tv.get_poly_df(avg_df, metrica='Tiempo')
        ytick_vals = list(range(0, max(TT_df['T_viaje'].values.tolist()), 30))
        ytick_labels = [str(datetime.timedelta(seconds=t)) for t in range(0, max(TT_df['T_viaje'].values.tolist()), 30)]
        y_axis_title = 'Tiempo de viaje [s] <br> </b>'
    else:
        keys = ['Velocidad', 'V_avg', 'V_poly']
        avg_df = tv.get_avg_df(TT_df, avg_time, metrica='Velocidad')
        poly_df = tv.get_poly_df(avg_df, metrica='Velocidad')
        ytick_vals = list(range(0, 70, 10))
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
                   marker=dict(color='yellow', size=5),
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
            'hovermode': 'closest',
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

if __name__ == '__main__':
    app.run_server(host='192.168.255.219', port=5000, debug=True)


