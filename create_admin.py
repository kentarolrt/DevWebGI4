import sys
sys.path.append('.')

from main import app
import utils

USERNAME   = 'admin'
PASSWORD   = 'admin123'
FIRSTNAME  = 'Admin'
LASTNAME   = 'OsmHome'
EMAIL      = 'admin@osmhome.fr'

with app.app_context():
    success, token = utils.createUser(USERNAME, PASSWORD, LASTNAME, FIRSTNAME, EMAIL, '30', 'male', '1995-01-01', 'père')
    if success:
        utils.verifyEmail(token)
        print(f'Admin créé — login: {USERNAME} / mdp: {PASSWORD}')
    else:
        print(f'Erreur : {token}')
