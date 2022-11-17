from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
import fonctions
import zeep
import folium

app = Flask(__name__)
app.debug = True
bootstrap = Bootstrap(app)
@app.route('/', methods =["GET","POST"])
def index():
    if request.method == 'GET':
        list_vehicule = fonctions.api_chargetrip_vehicles()
        modeles_vehicule = []
        for vehicule in list_vehicule:
            modeles_vehicule.append(vehicule)
        return render_template('index.html', modeles = modeles_vehicule)
    
    if request.method == 'POST':
        autonomie_voiture = fonctions.get_autonomie_voiture()
        ville_depart = request.form.get("ville_depart")
        region_depart = request.form.get("region_depart")
        ville_arrivee = request.form.get("ville_arrivee")
        region_arrivee = request.form.get("region_arrivee")
        vitesse = request.form.get("vitesse")
        coordonnees = fonctions.get_geocode_formulaire(ville_depart,region_depart,ville_arrivee,region_arrivee)
        directions = fonctions.get_directions(coordonnees[0], coordonnees[1], coordonnees[2], coordonnees[3])
        distance_trajet = fonctions.get_distance_trajet(coordonnees[0], coordonnees[1], coordonnees[2], coordonnees[3])
        nbr_trajet = fonctions.client_soap(distance_trajet, autonomie_voiture)
        temps_trajet = fonctions.temps_trajet(distance_trajet, vitesse)
        carte = fonctions.draw_trip(directions, coordonnees[0], coordonnees[1], coordonnees[2], coordonnees[3], autonomie_voiture, distance_trajet, nbr_trajet)
        return render_template('map.html',Carte=carte._repr_html_(), autonomie_voiture=autonomie_voiture, ville_depart=ville_depart, ville_arrivee=ville_arrivee, vitesse=vitesse, distance_trajet=distance_trajet, temps_trajet=temps_trajet)
        