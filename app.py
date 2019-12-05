from helper import lectura_archivos as rf
from helper import tiempoViaje as tv
import plotly.graph_objs as go
import datetime
import dash
import dash_core_components as dcc
import dash_html_components as html
import os
import glob
import pandas as pd
from dash.dependencies import Input, Output

csalles_dir = os.path.abspath('/Users/Joni/Documents/matriz-OD/02_identificacion-archivos/Logs-U4-campos-salles')
pico_dir = os.path.abspath('/Users/Joni/Documents/matriz-OD/02_identificacion-archivos/Logs-U5-pico')

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

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = 'Proyecto GCBA'

colors = {
    'background': '#ffffff',
    'text': '#111111'
}

app.layout = html.Div([
    html.Div([
        html.Div([
            html.Div([
                html.Label("Intervalo de tiempo para calcular "
                           "el promedio. [min]"),
            ], style={'position': 'relative','fontSize':'10pt'}),

            dcc.Input(
                        id="input-min",
                        type="number",
                        value=5,
                        placeholder="Tiempo para promedio",
                        debounce=True
                    ),
        ],style={'width': '25%','position': 'relative','left':'15px' ,'display': 'inline-block'}),
        html.Div([
            html.Div([
                html.Label('Tipo de gráfico'),
            ], style={'position': 'relative','top':'-7px','left':'10px','fontSize':'10pt'}),
            dcc.RadioItems(
                                    id = 'grafico-opt',
                                    options=[
                                        {'label': 'Tiempo de viaje', 'value': 'TT'},
                                        {'label': 'Velocidad', 'value': 'Vel'}
                                    ],
                                    value='TT',
                                    labelStyle={'display': 'inline-block'}
                                )
                    ],style={'width': '20%', 'position': 'relative','left':'30px', 'display': 'inline-block'})
    ],style = {'position': 'relative','top':'80px'}),
    html.Div([
        dcc.Graph(
                    id='graph-with-input',
                )
    ],style={'width':'75%','position': 'relative','top':'80px'})
])


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
                   marker=dict(color='black', size=3),
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


if __name__ == '__main__':
    app.run_server(host='10.78.162.120', port=5000, debug=False, dev_tools_ui=True, dev_tools_props_check=False)


