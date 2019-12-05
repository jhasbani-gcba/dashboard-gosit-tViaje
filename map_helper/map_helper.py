import requests

def get_layer(trayecto):
    layer = [dict(sourcetype="geojson",
                  source={
                      "type": "FeatureCollection",
                      "features": [
                          {
                              "type": "Feature",
                              "properties": {},
                              "geometry": {
                                  'type': 'LineString',
                                  'coordinates': trayecto
                              }
                          }
                      ]
                  },
                  type='line',
                  color='green',
                  line={'width': 3}
                  )
             ]
    return layer

def mapbox_request(route, token):
    base_url = 'https://api.mapbox.com/directions/v5/mapbox/driving/'
    url = base_url + str(route['origen_lon']) + \
          ',' + str(route['origen_lat']) + \
          ';' + str(route['destino_lon']) + \
          ',' + str(route['destino_lat'])
    params = {
        'geometries': 'geojson',
        'access_token': token
    }
    req = requests.get(url, params=params)
    route_json = req.json()
    coordinates = route_json['routes'][0]['geometry']['coordinates']
    return coordinates
