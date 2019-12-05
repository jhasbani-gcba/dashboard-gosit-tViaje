import pandas as pd
import numpy as np

def file_to_df(filename):

    if ".csv" in filename:
        df_file = pd.read_csv(filename,sep=";")
        patentes = df_file["Patente"].values.tolist()
        fecha_format = [ fecha.split(" ")[0]+'T'+fecha.split(" ")[1] for fecha in df_file["Fecha"].values.tolist() ]
        data = {'Patente':patentes, 'Fecha': fecha_format}
        df = pd.DataFrame(data).sort_values('Fecha')
        df.drop_duplicates(subset = ['Patente','Fecha'],keep='first',inplace=True)
    if ".log" in filename:
        f = open(filename,"r")
        data_patentes = []
        data_fecha = []
        for i,line in enumerate(f.readlines()):
            if i == 0:
                line_split = line.split("/")
                fecha = line_split[2][0:4]+'-'+line_split[1]+'-'+line_split[0]
            if i > 1:
                line_split = line.split(";")
                patente = line_split[4].split("=")[1]
                data_patentes.append(patente.strip())
                hour_read = line_split[1].split("=")[1].split(':')
                hora = hour_read[0][1:]+':'+hour_read[1]+':'+hour_read[2]
                fecha_format = fecha+'T'+hora
                data_fecha.append(fecha_format)
        f.close()
        data = {'Patente':data_patentes, 'Fecha': data_fecha}
        df = pd.DataFrame(data, columns = ["Patente","Fecha"])
        df.drop_duplicates(subset = 'Fecha',keep='first',inplace=True)
    return df

def str_to_datetime(fecha):
    
    return np.datetime64(fecha, dtype='M8[s]')

def get_pat_excl_dict(df,thr):
    fechas = df['Fecha'].values.tolist()
    patentes = df['Patente'].values.tolist()
    dict_ = {}
    for i,patente in enumerate(patentes):
        if patente not in dict_.keys():
            dict_[patente] =[fechas[i]]
        else:
            values = dict_[patente]
            values.append(fechas[i])
            dict_[patente] = values
    dict_excl = {}
    thr = thr*60
    for key, values in dict_.items():
        thr = np.timedelta64(thr,'s')
        i = 0
        j = 1
        excluir = []
        if len(values) > 1:
            while j < len(values):
                if (str_to_datetime(values[j]) - str_to_datetime(values[i])) < thr : 
                    excluir.append(values[j])
                    j += 1
                else:
                    i = j
                    j += 1
        if len(excluir)!=0:
            dict_excl[key] = excluir
    return dict_excl

def filtrar_patentes(df,thr):

    pat_exclude_dict = get_pat_excl_dict(df,thr)
    patentes = df['Patente'].values.tolist()
    fecha = df['Fecha'].values.tolist()
    
    patentes_filtradas = []
    fecha_filtrada = []

    for i,pat in enumerate(patentes):

        if pat in pat_exclude_dict.keys():
            if str(fecha[i]) not in pat_exclude_dict[pat]:
             
                patentes_filtradas.append(pat)
                fecha_filtrada.append(str(fecha[i])) 
        else:
            patentes_filtradas.append(pat)
            fecha_filtrada.append(str(fecha[i]))
        
    data = list(zip(patentes_filtradas,fecha_filtrada))
    df_filtrado = pd.DataFrame(data,columns = ["Patente","Fecha"])
    return df_filtrado


def count_OinD(comb):
    """
    Función que cuenta las ocurrencias de cada  patente del orígen en el destino
    :param comb:  - combinacion de dos archivos
    :return n: - numero de ocurrencias
    """
    n = 0
    O_df = comb[0]
    D_df = comb[1]
    for pat in O_df['Patente'].values.tolist():
        if pat in D_df['Patente'].values.tolist():
            n += 1
    return n


def get_OD_df(files_O, files_D, verbose=False):
    """
    Función que recibe el par de archivos de orígen y destino, y devuelve los dataframes de orígen y destino en el
    sentido que corresponde.
    :param files_O: - par de archivos del origen
    :param files_D: - par de archivos del destino
    :param verbose: - default False - opcion de que se imprima la combinacion correcta con el numero de ocurrencias
    :return O_df, D_df:
    """
    origen_1 = file_to_df(files_O[0])
    origen_2 = file_to_df(files_O[1])
    destino_1 = file_to_df(files_D[0])
    destino_2 = file_to_df(files_D[1])

    O1_df = filtrar_patentes(origen_1, 3)
    O2_df = filtrar_patentes(origen_2, 3)
    D1_df = filtrar_patentes(destino_1, 3)
    D2_df = filtrar_patentes(destino_2, 3)

    comb = [[O1_df, D1_df], [O1_df, D2_df], [O2_df, D1_df], [O2_df, D2_df]]
    data_str = ['O1 a D1', 'O1 a D2', 'O2 a D1', 'O2 a D2']

    result = []
    for i, data in enumerate(comb):
        n = count_OinD(data)
        result.append(n)

    best_ind = result.index(max(result))
    if verbose:
        print('El sentido correcto es {} con {} registros'.format(data_str[best_ind], result[best_ind]))

    return comb[best_ind][0], comb[best_ind][1]

def get_OD_dict(O_df, D_df):
    """
    Funcion que obtiene los diccionarios a partir de los dataframes de origen y destino.
    :param O_df: - pandas dataframe del origen
    :param D_df: -pandas dataframe del destino
    :return O_dict, D_dict: - diccionarios para el origen y destino con key = Patente y value = tiempo de captura
    """
    pat_origen = O_df['Patente'].values.tolist()
    pat_destino = D_df['Patente'].values.tolist()

    O_dict = {}
    D_dict = {}
    for pat in pat_destino:
        if pat in pat_origen:
            t_origen = [str(O_df['Fecha'].values.tolist()[i]) for i, pat_or in enumerate(pat_origen) if pat_or == pat]
            t_dest = [str(D_df['Fecha'].values.tolist()[i]) for i, pat_dest in enumerate(pat_destino) if pat_dest == pat]

            O_dict[pat] = t_origen
            D_dict[pat] = t_dest
    return O_dict, D_dict