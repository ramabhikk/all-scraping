import pandas as pd
import requests
from geopy.distance import great_circle
from tqdm import tqdm
tqdm.pandas()

API = 'AIzaSyDkQoei7Vj1QtgY62aKyyj4lRLvLgXKMVw'


df = pd.read_csv("GB Train stations.csv")
stores = pd.read_csv("stores.csv")

def get_gdistance(origin, dest):
    url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={origin[0]},{origin[1]}&destinations={dest[0]},{dest[1]}&key={API}"

    response = requests.request("GET", url, timeout=30)
    return response.json()['rows'][0]['elements'][0]['distance']['value']

def apply_gdistance(row, cords):
    store = (row['Latitude'], row['Longitude'])
    
    row['G_Distance'] = get_gdistance(store, cords)
    return row

def apply_distance(row, coordinates):
    store = (row['Latitude'], row['Longitude'])
    
    row['Distance'] = great_circle(store, coordinates).m
    return row  

def apply_nearby(row, stores, gmaps=False):
    cords = (row['Latitude'], row['Longitude'])
    df = stores.copy()
    df = df.apply(lambda x: apply_distance(x, cords), axis=1)
    
    d = df[df['Distance'] <= 2000]
    if d.empty:
        return row
    
    if gmaps:
        d = d.apply(lambda x: apply_gdistance(x, cords), axis = 1)
        d = d[d['G_Distance'] <= 2000]
        d = d.sort_values('G_Distance').reset_index(drop=True)
      
    
    for index, r in d.iterrows():
        row[f'Store_{index+1}_name'] = r['Fascia']
        row[f'Source_Store_{index+1}'] = r['Source']
        row[f'PostCode_Store_{index+1}'] = r['Postcode']
        row[f'TalysisID_Store_{index+1}'] = r['Talysis Id']
        row[f'Latitude_Store_{index+1}'] = r['Latitude']
        row[f'Longitude_Store_{index+1}'] = r['Longitude']
        if gmaps:
            row[f'GMaps Distance_Store_{index+1} m'] = r['G_Distance']
        else:
            row[f'Distance_Store_{index+1} m'] = r['Distance']
    
    return row


#d = df[:50]
d = df
a = d.progress_apply(lambda x: apply_nearby(x, stores, gmaps=True), axis=1)


length = len(list(a.columns))

columns = ['Station','Postcode','Latitude','Longitude','Owner']
length -= 5

count = int(length / 7)

for l in range(count):
    columns.append(f'Store_{l+1}_name')
    columns.append(f'Source_Store_{l+1}')
    columns.append(f'PostCode_Store_{l+1}')
    columns.append(f'TalysisID_Store_{l+1}')
    columns.append(f'Latitude_Store_{l+1}')
    columns.append(f'Longitude_Store_{l+1}')
    columns.append(f'GMaps Distance_Store_{l+1} m')
    
a = a[columns]

a.to_excel("Full_station.xlsx", index=False)