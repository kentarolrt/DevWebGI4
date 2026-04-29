import sys
sys.path.append('.')

from main import app
import utils

USERNAME = 'testuser'
PASSWORD = 'test123'

with app.app_context():
    existing = utils.getUser(USERNAME)
    if existing:
        utils.deleteUser(USERNAME)
        print(f'Utilisateur "{USERNAME}" supprimé.')

    success, token = utils.createUser(
        USERNAME, PASSWORD,
        lastname='Test', firstname='User',
        email='testuser@osmhome.fr',
        age='20', gender='male', birthdate='2004-01-01',
        member_type='fils'
    )
    if success:
        utils.verifyEmail(token)
        print(f'Utilisateur "{USERNAME}" créé — login: {USERNAME} / mdp: {PASSWORD}')
    else:
        print(f'Erreur lors de la création : {token}')
