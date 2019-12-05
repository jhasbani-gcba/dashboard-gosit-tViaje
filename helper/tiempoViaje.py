import pandas as pd
import numpy as np
import datetime
from sklearn.metrics import r2_score
import warnings


def str_to_datetime(fecha):
    return np.datetime64(fecha, dtype='M8[s]')

def get_ttravel_df(origen, destino,thr, distancia):
    
    pat_origen = origen['Patente'].values.tolist()
    pat_destino = destino['Patente'].values.tolist()

    origen_dict = {}
    destino_dict = {}
    for pat in pat_destino:
        if pat in pat_origen:
            t_origen = [origen['Fecha'].values.tolist()[i] for i,pat_or in enumerate(pat_origen) if pat_or == pat]
            t_dest = [destino['Fecha'].values.tolist()[i] for i,pat_dest in enumerate(pat_destino) if pat_dest == pat]
            origen_dict[pat] = t_origen
            destino_dict[pat] = t_dest
            
    t_viaje = {}
    thr = thr*60
    for key in destino_dict.keys():
        if len(origen_dict[key]) == len(destino_dict[key]):
            if len(destino_dict[key]) == 1:
                t = str_to_datetime(destino_dict[key][0]) - str_to_datetime(origen_dict[key][0])
                t = int(t.astype('m8[s]').astype('int'))
                #print(t)
                if t > 0 and t < thr:
                    t_viaje[destino_dict[key][0]] = t
            else:
                for i, t_d in enumerate(destino_dict[key]):
                    t = str_to_datetime(t_d) - str_to_datetime(origen_dict[key][i])
                    t = int(t.astype('m8[s]').astype('int'))
                if t > 0 and t < thr:
                    t_viaje[t_d] = t
        
    hora = list(t_viaje.keys())
    tiempo = []
    for key in t_viaje.keys():
        tiempo.append( t_viaje[key])

    tiempo_str = [str(datetime.timedelta(seconds=t)) for t in tiempo]
    velocidad = [(distancia/t)*3.6 for t in tiempo]
    
    patente = [destino['Patente'].loc[destino.index[destino['Fecha']==hr]].values[0] for hr in hora]
    data = list(zip(patente,hora,tiempo,tiempo_str,velocidad))

    tiempoDeViaje_df = pd.DataFrame(data, columns = ['Patente','Hora','T_viaje','T_viaje_str','Velocidad'])
    tiempoDeViaje_df = tiempoDeViaje_df.sort_values(by='Hora')
    
    return tiempoDeViaje_df

def get_avg_df(df, period, metrica='Tiempo'):
    avg = []
    window = []
    fecha_i = df['Hora'].values.tolist()[0][0:10]
    fecha_f = df['Hora'].values.tolist()[len(df['Hora'].values.tolist())-1][0:10]
    to = np.datetime64(fecha_i+'T'+'00:00:00',dtype = 'M8[s]')
    intervalo = np.timedelta64(period,'m')
    tf = to + intervalo
    horas = df['Hora'].values.tolist()
    if metrica == 'Tiempo':
        t_viaje = df['T_viaje'].values.tolist()
    elif metrica == 'Velocidad':
        t_viaje = df['Velocidad'].values.tolist()
    else:
        print('Error: metrica no valida')
        return
    
    
    avg.append(t_viaje[0])
        
    for i,hora in enumerate(horas):
       
        if to < str_to_datetime(hora) < tf:
            window.append(t_viaje[i])
        else:
            if len(window)==0:
                window.append(avg[len(avg)-1])
            avg.append(np.array(window).mean())
            to += intervalo
            tf += intervalo
            window = []
            if to < str_to_datetime(hora) < tf:
                window.append(t_viaje[i])
                
    window = [t_viaje[i] for i,hora in enumerate(horas) if tf-intervalo<str_to_datetime(hora)<tf]
    avg.append(np.array(window).mean())
    
    ti = np.datetime64(fecha_i+'T'+'00:00:00', dtype='M8[s]')
    tf = np.datetime64(fecha_f+'T'+'23:59:59', dtype='M8[s]')
    hr_Tmin = np.arange(ti,tf,intervalo)
    hr_Tmin=np.append(hr_Tmin,tf)
    #print(len(hr_Tmin),len(avg))
    #print(avg)
    if metrica == 'Tiempo':
        data = {'Hora': list(hr_Tmin.astype('M8[s]').astype('str')), 'T_viaje_avg': avg}
    elif metrica == 'Velocidad':
        data = {'Hora': list(hr_Tmin.astype('M8[s]').astype('str')), 'V_avg': avg}
    avg_df = pd.DataFrame(data)
    return avg_df


def get_poly_df(df, metrica = 'Tiempo'):
    x_str = df['Hora'].values.tolist()
    if metrica == 'Tiempo':
        y = df['T_viaje_avg'].values.tolist()
    elif metrica == 'Velocidad':
        y = df['V_avg'].values.tolist()
    else:
        print('Error: metrica no valida')
        return
    
    
    fecha_i = df['Hora'].values.tolist()[0][0:10]
    fecha_f = df['Hora'].values.tolist()[len(df['Hora'].values.tolist())-1][0:10]
    h_0 = np.datetime64(fecha_i+'T00:00:00',dtype = 'M8[s]').astype('int')
    
    x = []
    x_fit = []
    hora_poly =[]
    x.append(0)
    hora_poly.append(np.datetime64(fecha_i+'T00:00:00',dtype = 'M8[s]'))
    
    h_0 = np.datetime64(fecha_i+'T00:00:00',dtype = 'M8[s]').astype('int')
    for hora_str in x_str:
        x.append(str_to_datetime(hora_str).astype('int')-h_0)
        x_fit.append(str_to_datetime(hora_str).astype('int')-h_0)
        hora_poly.append(str_to_datetime(hora_str))
    x.append(24*3600)
    hora_poly.append(np.datetime64(fecha_f+'T23:59:59',dtype = 'M8[s]'))
    
    R2_list = []
    for deg in range(1, 30):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            p = np.poly1d(np.polyfit(x_fit, y, deg))
        R2_list.append(r2_score(y, p(x_fit)))
    p_deg = R2_list.index(max(R2_list))
    p = np.poly1d(np.polyfit(x_fit, y, p_deg))
    
    if metrica == 'Tiempo':
         data = {'Hora':hora_poly, 'T_viaje_poly':p(x)}
    elif metrica == 'Velocidad':
         data = {'Hora':hora_poly, 'V_poly':p(x)}
    
    poly_df = pd.DataFrame(data)
    return poly_df
