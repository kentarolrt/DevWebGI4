import sys
sys.path.append('.')

from main import app
import utils

services = [
    ('Surveillance Caméras',    'Accès en temps réel aux flux vidéo de toutes les caméras',          'Sécurité',      'restreint'),
    ('Alarme Intrusion',        'Système d\'alarme anti-intrusion centralisé avec alertes SMS',       'Sécurité',      'restreint'),
    ('Gestion des Accès',       'Configuration des codes et autorisations d\'accès à la maison',      'Sécurité',      'restreint'),
    ('Détection Fuites',        'Alertes instantanées en cas de fuite d\'eau détectée',               'Sécurité',      'libre'),
    ('Suivi Consommation',      'Monitoring de la consommation électrique en temps réel',             'Énergie',       'libre'),
    ('Alertes Énergie',         'Notifications automatiques en cas de surconsommation',               'Énergie',       'libre'),
    ('Gestion Solaire',         'Optimisation et supervision de la production d\'énergie solaire',    'Énergie',       'restreint'),
    ('Thermostat Intelligent',  'Programmation automatique du chauffage selon les habitudes',         'Confort',       'libre'),
    ('Volets Automatiques',     'Gestion automatisée des volets selon l\'heure et la luminosité',     'Confort',       'libre'),
    ('Éclairage Ambiant',       'Scénarios d\'éclairage personnalisables par pièce et ambiance',      'Confort',       'libre'),
    ('Streaming Musique',       'Diffusion musicale synchronisée dans toutes les pièces',             'Multimédia',    'libre'),
    ('Contrôle TV',             'Pilotage centralisé des écrans et box connectés',                    'Multimédia',    'libre'),
    ('Scénario Bonne Nuit',     'Éteint tout et sécurise la maison en un seul clic',                 'Automatisation','libre'),
    ('Scénario Départ',         'Prépare la maison au départ : chauffage, alertes, sécurité',         'Automatisation','libre'),
    ('Routines Programmées',    'Automatisations planifiées par heure et jour de la semaine',         'Automatisation','libre'),
    ('Backup Configurations',   'Sauvegarde automatique de toutes les configurations domotiques',     'Automatisation','restreint'),
    ('Qualité de l\'air',       'Surveillance en continu du CO₂, de l\'humidité et température',      'Santé',         'libre'),
    ('Alertes Santé',           'Notifications en cas d\'anomalie environnementale détectée',         'Santé',         'libre'),
    ('Suivi Activité',          'Synchronisation et analyse des données de la montre connectée',      'Santé',         'libre'),
    ('Rapport Hebdomadaire',    'Résumé hebdomadaire complet de l\'utilisation de la maison',         'Automatisation','libre'),
]

with app.app_context():
    db = utils.openDB()
    db.executemany(
        'INSERT INTO services (name, description, category, access) VALUES (?, ?, ?, ?)',
        services
    )
    db.commit()
    print(f'{len(services)} services insérés.')
