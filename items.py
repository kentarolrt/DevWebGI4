import sys
sys.path.append('.')

from main import app
import utils

objets = [
    ('Thermostat Salon',    'Contrôle la température du salon',             'thermostat',  'Nest',       'actif',   'Wi-Fi',      85,  'Salon'),
    ('Thermostat Chambre',  'Contrôle la température de la chambre',        'thermostat',  'Nest',       'actif',   'Wi-Fi',      72,  'Chambre'),
    ('Caméra Entrée',       'Surveille l\'entrée principale',               'caméra',      'Arlo',       'actif',   'Wi-Fi',      60,  'Entrée'),
    ('Caméra Jardin',       'Surveille le jardin extérieur',                'caméra',      'Arlo',       'inactif', 'Wi-Fi',      15,  'Jardin'),
    ('Ampoule Cuisine',     'Éclairage intelligent cuisine',                'éclairage',   'Philips Hue','actif',   'Zigbee',     None,'Cuisine'),
    ('Ampoule Salon',       'Éclairage intelligent salon',                  'éclairage',   'Philips Hue','actif',   'Zigbee',     None,'Salon'),
    ('Serrure Entrée',      'Serrure connectée de la porte principale',     'serrure',     'Yale',       'actif',   'Bluetooth',  90,  'Entrée'),
    ('Capteur Fumée',       'Détecte la fumée et le monoxyde de carbone',   'capteur',     'Nest',       'actif',   'Wi-Fi',      95,  'Cuisine'),
    ('Capteur Mouvement',   'Détecte les mouvements dans le couloir',       'capteur',     'Philips Hue','actif',   'Zigbee',     80,  'Couloir'),
    ('Aspirateur Robot',    'Aspiration automatique des sols',              'aspirateur',  'Roomba',     'actif',   'Wi-Fi',      45,  'Salon'),
    ('Lave-vaisselle',      'Lave-vaisselle connecté avec programme auto',  'électroménager','Samsung',  'inactif', 'Wi-Fi',      None,'Cuisine'),
    ('Machine à laver',     'Lave-linge connecté avec suivi consommation',  'électroménager','LG',       'actif',   'Wi-Fi',      None,'Buanderie'),
    ('Volet Salon',         'Volet roulant motorisé du salon',              'volet',       'Somfy',      'actif',   'Z-Wave',     None,'Salon'),
    ('Volet Chambre',       'Volet roulant motorisé de la chambre',         'volet',       'Somfy',      'inactif', 'Z-Wave',     None,'Chambre'),
    ('Montre Connectée',    'Suivi activité et santé du membre',            'montre',      'Fitbit',     'actif',   'Bluetooth',  55,  None),
    ('Frigo Connecté',      'Réfrigérateur avec inventaire automatique',    'électroménager','Samsung',  'actif',   'Wi-Fi',      None,'Cuisine'),
    ('Capteur Eau',         'Détecte les fuites d\'eau sous l\'évier',      'capteur',     'Fibaro',     'actif',   'Z-Wave',     70,  'Cuisine'),
    ('Panneau Solaire',     'Gestion de la production d\'énergie solaire',  'énergie',     'SolarEdge',  'actif',   'Wi-Fi',      None,'Toit'),
    ('Compteur Énergie',    'Mesure la consommation électrique globale',    'énergie',     'Schneider',  'actif',   'Wi-Fi',      None,'Garage'),
    ('Interphone Vidéo',    'Interphone avec caméra et déverrouillage',     'caméra',      'Ring',       'actif',   'Wi-Fi',      None,'Entrée'),
]

with app.app_context():
    db = utils.openDB()
    db.executemany(
        '''INSERT INTO devices 
           (name, description, type, brand, status, connectivity, battery, room) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        objets
    )
    db.commit()