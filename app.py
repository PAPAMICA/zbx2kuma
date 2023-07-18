#!/usr/local/bin/python3

import requests
import json
import os
from uptime_kuma_api import UptimeKumaApi
from uptime_kuma_api import MonitorType,IncidentStyle


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
            "selectProblemEvents": "extend",
            "selectTags": "extend"
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


# Vérification des variables d'environnement
required_env_vars = ['ZABBIX_URL', 'ZABBIX_USERNAME', 'ZABBIX_PASSWORD', 'KUMA_URL', 'KUMA_USERNAME', 'KUMA_PASSWORD']

missing_env_vars = [var for var in required_env_vars if var not in os.environ]

if missing_env_vars:
    print("Les variables d'environnement suivantes ne sont pas configurées :")
    for var in missing_env_vars:
        print(var)
    exit()


zabbix_url = os.environ.get('ZABBIX_URL') + '/api_jsonrpc.php'
zabbix_username = os.environ.get('ZABBIX_USERNAME')
zabbix_password = os.environ.get('ZABBIX_PASSWORD')

auth_token = zabbix_login(zabbix_url, zabbix_username, zabbix_password)
status = zabbix_get_status(zabbix_url, auth_token)
#print(status)

monitors = []
statuspages = []
tags = []
with UptimeKumaApi(os.environ.get('KUMA_URL')) as api:
    api.login(os.environ.get('KUMA_USERNAME'), os.environ.get('KUMA_PASSWORD'))
    monitors_list = api.get_monitors()
    for monitor in monitors_list:
        monitors.append({
                "id": monitor['id'],
                "name": monitor['name']
            })
    tag_list = api.get_tags()
    for tag in tag_list:
        tags.append({
                "id": tag['id'],
                "name": tag['name']
            })
    statuspages_list = api.get_status_pages()
    for statuspage in statuspages_list:
        statuspages.append(statuspage['slug'])

    if 'zbx2kuma' not in statuspages:
        api.add_status_page("zbx2kuma", "zbx2kuma")
        print(f"Statuspage zbx2kuma Added !")
    else:
        print(f"Statuspage zbx2kuma already exist !")

    monitors_id_list = []
    events_list = []
    categories = []




    for item in status:
        if 'parents' in item and len(item['parents']) > 0:
            for parent in item['parents']:
                if parent['name'] not in [tag['name'] for tag in tags]:
                    tag_added = api.add_tag(
                        name=parent['name'],
                        color="#0098FF"
                    )
                    tags.append({
                        "id": tag_added['id'],
                        "name": tag_added['name']
                    })
                    print(f"Tag {parent['name']} Added !")
                else:
                    print(f"Tag {parent['name']} already exist !")

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
        
        
        
        if 'parents' in item and len(item['parents']) > 0:  # Edited line
            print(f"\n\nNom: {item['name']}\n → Statut: {status_text}")
            if 'problem_events' in item and len(item['problem_events']) > 0:
                for event in item['problem_events']:
                    print(f" → Event ID: {event['eventid']} - {event['name']}")
                    events_list.append({
                        "source": item['name'],
                        "name": event['name'],
                        "eventid": event['eventid']
                    })
                
        
        

        if 'parents' in item and len(item['parents']) > 0:
            if item['name'] not in [monitor['name'] for monitor in monitors]:
                kuma_monitor=next((tag['value'] for tag in item['tags'] if tag['tag'] == 'kuma.monitor'), None)
                


                monitor_added = api.add_monitor(
                    
                    type= MonitorType.HTTP if kuma_monitor == 'HTTP' else MonitorType.PORT if kuma_monitor == 'PORT' else MonitorType.PING if kuma_monitor == 'PING' else MonitorType.KEYWORD if kuma_monitor == 'KEYWORD' else MonitorType.GRPC_KEYWORD if kuma_monitor == 'GRPC_KEYWORD' else MonitorType.DNS if kuma_monitor == 'DNS' else MonitorType.DOCKER if kuma_monitor == 'DOCKER' else MonitorType.PUSH if kuma_monitor == 'PUSH' else MonitorType.STEAM if kuma_monitor == 'STEAM' else MonitorType.GAMEDIG if kuma_monitor == 'GAMEDIG' else MonitorType.MQTT if kuma_monitor == 'MQTT' else MonitorType.SQLSERVER if kuma_monitor == 'SQLSERVER' else MonitorType.POSTGRES if kuma_monitor == 'POSTGRES' else MonitorType.MYSQL if kuma_monitor == 'MYSQL' else MonitorType.MONGODB if kuma_monitor == 'MONGODB' else MonitorType.RADIUS if kuma_monitor == 'RADIUS' else MonitorType.REDIS if kuma_monitor == 'REDIS' else MonitorType.GROUP,
                    name=item['name'],
                    #tag=item['parents'][0]['name'],
                    #url='https://traefik-' + item['name'] + '.papamica.net'
                    url=next((tag['value'] for tag in item['tags'] if tag['tag'] == 'kuma.url'), None)

                )

                for parent in item['parents']:
                    parent_tag = [tag['id'] for tag in tags if tag['name'] == parent['name']]
                    if parent_tag:
                        api.add_monitor_tag(
                            tag_id=parent_tag[0],
                            monitor_id=monitor_added['monitorID']
                        )
                print(f"Monitor {item['name']} Added !")
            else:
                print(f"Monitor {item['name']} already exist !")

    publicGroupList = []
    monitors_list = []
    monitors = []
    monitors_list = api.get_monitors()
    for monitor in monitors_list:
        #print(monitor)
        monitors.append({
                "id": monitor['id'],
                "name": monitor['name'],
                "tag": monitor['tags'][0]['name']
            })
    i=0
    for category in tags:
        monitors_id_list = []
        monitors_with_category = [monitor['id'] for monitor in monitors if monitor['tag'] == category['name']]
        for monitor in monitors_with_category:
            monitors_id_list.append({
                'id': monitor
            })
        i=i+1

        publicGroupList.append({
            'name': category['name'],
            'weight': i,
            'monitorList': monitors_id_list
        })

    #print(publicGroupList)

    api.save_status_page(
        slug="zbx2kuma",
        title="zbx2kuma",
        description="Page de status automatique avec Zabbix",
        publicGroupList=publicGroupList
    )
    content = ""
    print("\n\nMise à jour des événemments :")
    if events_list:
        for event in events_list:
            print(f"Evenement mis à jour : {event['source']} → {event['name']}")
            content = content + "\n\n**" +  event['source'] + "** → " + event['name']
        api.post_incident(
            slug="zbx2kuma",
            title="Incidents en cours",
            content=content,
            style=IncidentStyle.WARNING
            )
    else:
        print("Pas d'événemments !")
        api.unpin_incident(slug="zbx2kuma")
    api.disconnect()




