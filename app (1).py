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


zabbix_url = os.environ.get('ZABBIX_URL') + '/api_jsonrpc.php'
zabbix_username = os.environ.get('ZABBIX_USERNAME')
zabbix_password = os.environ.get('ZABBIX_PASSWORD')

auth_token = zabbix_login(zabbix_url, zabbix_username, zabbix_password)
status = zabbix_get_status(zabbix_url, auth_token)
print(status)

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




with UptimeKumaApi(os.environ.get('KUMA_URL')) as api:
    api.login(os.environ.get('KUMA_USERNAME'), os.environ.get('KUMA_PASSWORD'))
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

with UptimeKumaApi(os.environ.get('KUMA_URL')) as api:
    api.login(os.environ.get('KUMA_USERNAME'), os.environ.get('KUMA_PASSWORD'))
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
                monitor_added = api.add_monitor(
                    type=MonitorType.HTTP,
                    name=item['name'],
                    #tag=item['parents'][0]['name'],
                    url='https://traefik-' + item['name'] + '.papamica.net'
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

with UptimeKumaApi(os.environ.get('KUMA_URL')) as api:
    api.login(os.environ.get('KUMA_USERNAME'), os.environ.get('KUMA_PASSWORD'))
    api.save_status_page(
        slug="zbx2kuma",
        title="zbx2kuma",
        description="Page de status automatique avec Zabbix",
        publicGroupList=publicGroupList
    )
    content = ""
    if events_list:
        for event in events_list:
            content = content + "\n\n**" +  event['source'] + "** → " + event['name']
    # #print(f"{event['eventid']} - {event['name']}")
    # with UptimeKumaApi(os.environ.get('KUMA_URL')) as api:
    #     api.login(os.environ.get('KUMA_USERNAME'), os.environ.get('KUMA_PASSWORD'))
        api.post_incident(
            slug="zbx2kuma",
            title="Incidents en cours",
            content=content,
            style=IncidentStyle.WARNING
        )
        api.disconnect()




