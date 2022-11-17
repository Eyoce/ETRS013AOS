from calendar import c
from unittest import skip
import requests
import json
import pandas as pd
from flask import request
import folium
from zeep import Client
from time import *

#Méthode pour récupérer la liste des vehicules électriques, communication avec l'api de Chargetrip
def api_chargetrip_vehicles():
    url = 'https://api.chargetrip.io/graphql'
    headers = {
        "x-client-id": '634d7dfcd0930830249a0bb3',
        "x-app-id": '634d7dfcd0930830249a0bb5'
    }
    query = """
    query carListAll {
        carList {
            id
            naming {
                make
                model
                version
                edition
                chargetrip_version
            }
            adapters {
                standard
                power
                time
                speed
            }
            battery {
                usable_kwh
                full_kwh
            }
            range {
                chargetrip_range {
                    best
                    worst
                }
            }
            media {
                image {
                    id
                    type
                    url
                    height
                    width
                    thumbnail_url
                    thumbnail_height
                    thumbnail_width
                }
                brand {
                    id
                    type
                    url
                    height
                    width
                    thumbnail_url
                    thumbnail_height
                    thumbnail_width
                }
                video {
                    id
                    url
                }
            }
        }
    }
"""
    r = requests.post(url=url, json={'query': query}, headers=headers).json()
    list_vehicles = []
    for i in r['data']['carList']:
        make = i['naming']['make']
        model = i['naming']['model']
        version =  i['naming']['version']
        range = (i['range']['chargetrip_range']['best'] + i['range']['chargetrip_range']['worst']) / 2
        data = make,model,version,range
        list_vehicles.append(data)
    return(list_vehicles)

#Méthode pour récupérer la liste des bornes électriques, communication avec l'api de Chargetrip
def get_borne(latitude,longitude):
   coord_borne=[]
   headers = {
       'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
   }
   call = requests.get('https://api.openchargemap.io/v3/poi?maxresults=1&latitude='+str(latitude)+'&longitude='+str(longitude)+'&distanceunit=km&key=71ab4e08-4e73-49fa-9ae2-188a992755ad', headers=headers) 
   if (call.status_code==200):
       req_data = call.json()
       coord_borne=[req_data[0]['AddressInfo']['Latitude'],req_data[0]['AddressInfo']['Longitude']]
   else :
       coord_borne=call.status_code
   return coord_borne

#Intérogation de l'api openroute service afin de récupérer les coordonnées gps de la ville de départ et de la ville d'arrivée inscrite par l'utilisateur
def get_autonomie_voiture():
    autonomie = request.form.get("autonomie")
    autonomie_float = float(autonomie)
    autonomie_final = round(autonomie_float)
    return autonomie_final

#Méthode pour récupérer les coordonnées géographique de la ville de départ et de celle d'arrivée
def get_geocode_formulaire(ville_depart,region_depart,ville_arrivee,region_arrivee):
    api_key = "5b3ce3597851110001cf624853389a53d019457da05b1065d8b5567c"
    headers = {
    'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
    }
    geocodedepart = requests.get('https://api.openrouteservice.org/geocode/search?api_key=' +str(api_key) +'&text=' +str(ville_depart) +'%20' +str(region_depart), headers=headers)
    pointdepart = json.loads(geocodedepart.text)
    geopointdepart = pointdepart["features"][0]["geometry"]["coordinates"]
    lat_dep = geopointdepart[1]
    long_dep = geopointdepart[0]
    geocodearrivee = requests.get('https://api.openrouteservice.org/geocode/search?api_key=' +str(api_key) +'&text=' +str(ville_arrivee) + '%20' +str(region_arrivee), headers=headers)
    pointarrivee = json.loads(geocodearrivee.text)
    geopointarrivee = pointarrivee["features"][0]["geometry"]["coordinates"]
    lat_arr = geopointarrivee[1]
    long_arr = geopointarrivee[0]
    return(lat_dep, long_dep, lat_arr, long_arr)

#Méthode permettant de récupérer la distance :
def get_distance_trajet(lat_dep, long_dep, lat_arr, long_arr):
    api_key = "5b3ce3597851110001cf624853389a53d019457da05b1065d8b5567c"
    headers = {
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
    }
    ville_a = str(long_dep) + ',' + str(lat_dep)
    ville_b = str(long_arr) + ',' + str(lat_arr)
    url = "https://api.openrouteservice.org/v2/directions/driving-car?api_key=" + str(api_key) + "&start=" + str(ville_a) + "&end=" + str(ville_b)
    call = requests.get( url, headers=headers)
    distance=(call.json()['features'][0]['properties']['segments'][0]['distance'])/1000
    return (distance)

#Méthode permettant de récupérer les directions empruntés du départ vers l'arrivée, communication avec l'api d'openroute service directions
def get_directions(lat_dep, long_dep, lat_arr, long_arr):
    api_key = "5b3ce3597851110001cf624853389a53d019457da05b1065d8b5567c"
    headers = {
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
    }
    ville_a = str(long_dep) + ',' + str(lat_dep)
    ville_b = str(long_arr) + ',' + str(lat_arr)
    url = "https://api.openrouteservice.org/v2/directions/driving-car?api_key=" + str(api_key) + "&start=" + str(ville_a) + "&end=" + str(ville_b)
    call = requests.get(url, headers=headers)
    return (call)

#Méthode permettant de récupérer une liste comprenant toute les distance en km pour chaque direction
def get_distance_directions(call, autonomie_voiture):
    
    list_distance_direction = []
    autonomie_recharge = autonomie_voiture - 30
    etape = 0

    #Récupération de l'ensemble des distances par ensemble de waypoints
    while True:
        try:
            distance_direction = call.json()["features"][0]["properties"]["segments"][0]["steps"][etape]['distance']/1000
            distance_direction_float = float(distance_direction)
            distance_direction_final = round(distance_direction_float)
            list_distance_direction.append(distance_direction_final)
            etape = etape + 1
        except:
            break

    #Récupération de la longitude et de la latitude a partir de laquelle la voiture n'a plus assez d'autonomie pour finir le trajet
    compteur = 0
    y = 0
    while y < autonomie_recharge:
        y = y + list_distance_direction[compteur]
        compteur = compteur + 1
    
    #Interrogation afin de connaître le waypoint spécifique a partir duquel il faut rechercher une borne
    n_waypoint = call.json()["features"][0]["properties"]["segments"][0]["steps"][compteur]["way_points"][1]
    coord_recherche_borne = call.json()['features'][0]['geometry']['coordinates'][n_waypoint]


    #Call vers l'api des bornes avec les directions récupérées :
    borne = get_borne(coord_recherche_borne[0], coord_recherche_borne[1])
    return borne

def client_soap(distance,autonomie):
    #client = Client('http://127.0.0.1:3000/?wsdl')
    #result = client.service.calcul(distance,autonomie)
    #return result
    return 1

def temps_trajet(distance,vitesse):
    temps_trajet = (float(distance) / (float(vitesse))) * 3600
    temps_trajet_format = strftime('%H heures %M minutes %S secondes', gmtime(temps_trajet))
    return temps_trajet_format

#Méthode permettant d'afficher la carte et de tracer l'itinéraire via les directions récupérées précédemment
def draw_trip(call, lat_dep, long_dep, lat_arr, long_arr, autonomie_voiture, distance_trajet, nbr_trajet):
    point_depart = [lat_dep, long_dep]
    point_arrivee = [lat_arr, long_arr]
    ville_depart = request.form.get("ville_depart")
    ville_arrivee = request.form.get("ville_arrivee")
    if (float(autonomie_voiture) > float(distance_trajet)) :
        coords = call.json()['features'][0]['geometry']['coordinates']
        points = [[i[1], i[0]] for i in coords]
        carte = folium.Map()
        folium.Marker(point_depart, popup="<i>Départ</i>", tooltip=ville_depart, icon=folium.Icon(color="green")).add_to(carte)
        folium.Marker(point_arrivee, popup="<i>Arrivée</i>", tooltip=ville_arrivee, icon=folium.Icon(color="red")).add_to(carte)
        folium.PolyLine(points, weight=5, opacity=1).add_to(carte)
        df = pd.DataFrame(coords).rename(columns={0:'Lon', 1:'Lat'})[['Lat', 'Lon']]
        sw = df[['Lat', 'Lon']].min().values.tolist()
        ne = df[['Lat', 'Lon']].max().values.tolist()
        carte.fit_bounds([sw, ne])
        return carte
    else:
        coord_borne = get_distance_directions(call, autonomie_voiture)
        coord_borne_carte = [coord_borne[1], coord_borne[0]]
        trajet = []
        #i = 0
        #while(i < nbr_trajet)
        premier_trajet = get_directions(lat_dep, long_dep, coord_borne[1], coord_borne[0])
        second_trajet = get_directions(coord_borne[1], coord_borne[0], lat_arr, long_arr)
        coords1 = premier_trajet.json()['features'][0]['geometry']['coordinates']
        points1 = [[i[1], i[0]] for i in coords1]
        coords2 = second_trajet.json()['features'][0]['geometry']['coordinates']
        points2 = [[i[1], i[0]] for i in coords2]
        trajet.append(points1)
        trajet.append(points2)
        carte = folium.Map()
        folium.Marker(point_depart, popup="<i>Départ</i>", tooltip=ville_depart, icon=folium.Icon(color="green")).add_to(carte)
        folium.Marker(point_arrivee, popup="<i>Arrivée</i>", tooltip=ville_arrivee, icon=folium.Icon(color="red")).add_to(carte)
        folium.Marker(coord_borne_carte, popup="<i>Borne</i>", tooltip=coord_borne_carte, icon=folium.Icon(color="blue")).add_to(carte)
        folium.PolyLine(trajet, weight=5, opacity=1).add_to(carte)
        df = pd.DataFrame(trajet).rename(columns={0:'Lon', 1:'Lat'})[['Lat', 'Lon']]
        sw = df[['Lat', 'Lon']].min().values.tolist()
        ne = df[['Lat', 'Lon']].max().values.tolist()
        carte.fit_bounds([sw, ne])
        return carte