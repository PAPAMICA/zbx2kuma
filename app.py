import requests
import json
import os

def zabbix_login(url, username, password):
    """
    Fonction pour se connecter à Zabbix via l'API REST et obtenir un token d'authentification.
    """
    headers = {'Content-Type': 'application/json'}
    data = {
        'jsonrpc': '2.0',
        'method': 'user.login',
        'params': {
            'user': username,
            'password': password
        },
        'id': 1
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    result = response.json()

    if 'result' in result:
        return result['result']
    else:
        raise Exception('Échec de la connexion à Zabbix. Vérifiez vos informations d\'identification.')

def zabbix_get_status(url, auth_token):
    """
    Fonction pour obtenir les statuts depuis Zabbix via l'API REST.
    """
    headers = {'Content-Type': 'application/json'}
    data = {
        'jsonrpc': '2.0',
        "method": "service.get",
        "params": {
            "output": "extend",
            "selectChildren": "extend",
            "selectParents": "extend",
            "selectProblemEvents": "extend"
        },
        'auth': auth_token,
        'id': 1
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    result = response.json()

    if 'result' in result:
        return result['result']
    else:
        raise Exception('Échec de la récupération des statuts depuis Zabbix.')


zabbix_url = os.environ.get('ZABBIX_URL')
zabbix_username = os.environ.get('ZABBIX_USERNAME')
zabbix_password = os.environ.get('ZABBIX_PASSWORD')

auth_token = zabbix_login(zabbix_url, zabbix_username, zabbix_password)
status = zabbix_get_status(zabbix_url, auth_token)

for item in status:
    #print(dict(item))
    status_text = ""
    if item['status'] == "-1":
        status_text = "OK"
    elif item['status'] == "0":
        status_text = "Non classé"
    elif item['status'] == "1":
        status_text = "Information"
    elif item['status'] == "2":
        status_text = "Avertissement"
    elif item['status'] == "3":
        status_text = "Moyen"
    elif item['status'] == "4":
        status_text = "Haut"
    elif item['status'] == "5":
        status_text = "Urgent"
    
    print(f"\n\nNom: {item['name']}\n → Statut: {status_text}")
    if 'problem_events' in item and len(item['problem_events']) > 0:
        print(f" → Problème: {item['problem_events'][0]['name']}")
