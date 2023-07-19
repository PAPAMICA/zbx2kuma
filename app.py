import os
import warnings

import requests
from uptime_kuma_api import IncidentStyle, MonitorType, UptimeKumaApi


def zabbix_login(url, username, password):
    """Function to connect to Zabbix via the REST API
    and obtain an authentication token."""

    headers = {"Content-Type": "application/json"}
    data = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {"user": username, "password": password},
        "id": 1,
    }

    response = requests.post(url, headers=headers, json=data)
    result = response.json()

    if "result" in result:
        return result["result"]

    # FIXME: use a better exception type
    raise Exception("Failed to connect to Zabbix. Check your credentials.")


def zabbix_get_status(url, auth_token):
    """Function to retrieve statuses from Zabbix via the REST API."""

    headers = {"Content-Type": "application/json"}
    data = {
        "jsonrpc": "2.0",
        "method": "service.get",
        "params": {
            "output": "extend",
            "selectChildren": "extend",
            "selectParents": "extend",
            "selectProblemEvents": "extend",
            "selectTags": "extend",
        },
        "auth": auth_token,
        "id": 1,
    }

    response = requests.post(url, headers=headers, json=data)
    result = response.json()

    if "result" in result:
        return result["result"]

    # FIXME: use a better exception type
    raise Exception("Failed to retrieve statuses from Zabbix.")


# I would recommand using something like pydantic to validate
# the environment variables
# The presence of the envvar is checked in the code below,
# but not the type/pattern/...

# Define the required environment variables
required_env_vars = [
    "ZABBIX_URL",
    "ZABBIX_USERNAME",
    "ZABBIX_PASSWORD",
    "KUMA_URL",
    "KUMA_USERNAME",
    "KUMA_PASSWORD",
]

# Check if any required environment variables are missing
missing_env_vars = [var for var in required_env_vars if var not in os.environ]

# If any required environment variables are missing,
# print them and exit the program
if missing_env_vars:
    print("The following environment variables are not configured:")
    for var in missing_env_vars:
        print(var)
    exit(1)


# Get the Zabbix URL, username, and password from the environment variables
zabbix_url = os.environ.get("ZABBIX_URL") + "/api_jsonrpc.php"
zabbix_username = os.environ.get("ZABBIX_USERNAME")
zabbix_password = os.environ.get("ZABBIX_PASSWORD")

# Login to Zabbix and get the status
auth_token = zabbix_login(zabbix_url, zabbix_username, zabbix_password)
status = zabbix_get_status(zabbix_url, auth_token)
# print(status)

# Initialize lists for monitors, status pages, and tags
monitors = []
statuspages = []
tags = []

# Login to the UptimeKuma API and get the monitors, tags, and status pages
with UptimeKumaApi(os.environ.get("KUMA_URL")) as api:
    # why wont reuse already declared variables to  void duplicated code
    # and have a single source of thuth ?
    api.login(os.environ.get("KUMA_USERNAME"), os.environ.get("KUMA_PASSWORD"))
    monitors_list = api.get_monitors()
    for monitor in monitors_list:
        monitors.append({"id": monitor["id"], "name": monitor["name"]})
    tag_list = api.get_tags()
    for tag in tag_list:
        tags.append({"id": tag["id"], "name": tag["name"]})
    statuspages_list = api.get_status_pages()
    for statuspage in statuspages_list:
        statuspages.append(statuspage["slug"])

    # If the status page 'zbx2kuma' does not exist, add it
    if "zbx2kuma" not in statuspages:
        api.add_status_page("zbx2kuma", "zbx2kuma")
        print("Statuspage zbx2kuma Added !")
    else:
        print("Statuspage zbx2kuma already exist !")

    # Initialize lists for monitor IDs, events, and categories
    monitors_id_list = []
    events_list = []
    categories = []

    try:
        for item in status:
            for parent in item["parents"]:
                # expenential complexity here, take a look at sets or
                # any O(1) data structure
                if parent["name"] not in [tag["name"] for tag in tags]:
                    tag_added = api.add_tag(
                        name=parent["name"],
                        color="#0098FF",
                    )
                    tags.append(
                        {
                            "id": tag_added["id"],
                            "name": tag_added["name"],
                        }
                    )
                    print(f"Tag {parent['name']} Added !")
                else:
                    print(f"Tag {parent['name']} already exist !")
    except KeyError:
        # IDK what to put here as I don't know the business logic
        ...

    mapping = {
        "-1": "OK",
        "0": "Unclassified",
        "1": "Information",
        "2": "Warning",
        "3": "Medium",
        "4": "High",
        "5": "Urgent",
    }
    # Iterating over each item in status and setting status_text
    # based on item's status
    for item in status:
        try:
            status_text = mapping[item["status"]]
        except KeyError:
            status_text = "Unknown"
            warnings.warn(
                f"Unknown status {item['status']} for {item['name']}"
            )  # noqa E501

        # Checking if item has parents and printing item's name and status
        try:
            print(f"\nName: {item['name']}\n → Status: {status_text}")
            try:
                for event in item["problem_events"]:
                    print(f" → Event ID: {event['eventid']} - {event['name']}")
                    events_list.append(
                        {
                            "source": item["name"],
                            "name": event["name"],
                            "eventid": event["eventid"],
                        }
                    )
            except KeyError:
                pass
        except KeyError:
            warnings.warn(f"KeyError for {item['name']}")

        try:
            if item["name"] not in [monitor["name"] for monitor in monitors]:
                kuma_monitor = next(
                    (
                        tag["value"]
                        for tag in item["tags"]
                        if tag["tag"] == "kuma.monitor"
                    ),
                    None,
                )

                if kuma_monitor == "HTTP":
                    monitor_added = api.add_monitor(
                        type=MonitorType.HTTP,
                        name=item["name"],
                        url=next(
                            (
                                tag["value"]
                                for tag in item["tags"]
                                if tag["tag"] == "kuma.url"
                            ),
                            None,
                        ),
                    )
                elif kuma_monitor == "PORT":
                    monitor_added = api.add_monitor(
                        type=MonitorType.PORT,
                        name=item["name"],
                        hostname=next(
                            (
                                tag["value"]
                                for tag in item["tags"]
                                if tag["tag"] == "kuma.hostname"
                            ),
                            None,
                        ),
                        port=int(
                            next(
                                (
                                    tag["value"]
                                    for tag in item["tags"]
                                    if tag["tag"] == "kuma.port"
                                ),
                                None,
                            )
                        ),
                    )
                elif kuma_monitor == "PING":
                    monitor_added = api.add_monitor(
                        type=MonitorType.PING,
                        name=item["name"],
                        hostname=next(
                            (
                                tag["value"]
                                for tag in item["tags"]
                                if tag["tag"] == "kuma.hostname"
                            ),
                            None,
                        ),
                    )
                else:
                    warnings.warn(
                        f"Monitor type not supported : {kuma_monitor}"
                    )  # noqa E501

                for parent in item["parents"]:
                    parent_tag = [
                        tag["id"]
                        for tag in tags
                        if tag["name"] == parent["name"]  # noqa E501
                    ]
                    if parent_tag:
                        api.add_monitor_tag(
                            tag_id=parent_tag[0],
                            monitor_id=monitor_added["monitorID"],
                        )
                print(f"Monitor {item['name']} Added !")
            else:
                print(f"Monitor {item['name']} already exist !")
        except KeyError:
            warnings.warn(f"KeyError for {item['name']}")

    # Initializing lists and getting monitors
    publicGroupList = []
    monitors_list = []
    monitors = []
    monitors_list = api.get_monitors()
    for monitor in monitors_list:
        # print(monitor)
        monitors.append(
            {
                "id": monitor["id"],
                "name": monitor["name"],
                "tag": monitor["tags"][0]["name"],
            }
        )

    # Iterating over each category in tags
    for i, category in enumerate(tags):
        monitors_id_list = []
        monitors_with_category = [
            monitor["id"] for monitor in monitors if monitor["tag"] == category["name"] # noqa E501
        ]
        for monitor in monitors_with_category:
            monitors_id_list.append({"id": monitor})

        publicGroupList.append(
            {
                "name": category["name"],
                "weight": i,
                "monitorList": monitors_id_list,
            }
        )

    # print(publicGroupList)

    # Saving status page
    api.save_status_page(
        slug="zbx2kuma",
        title="zbx2kuma",
        description="Automatic status page with Zabbix → https://github.com/PAPAMICA/zbx2kuma", # noqa E501
        publicGroupList=publicGroupList,
    )

    # Create events
    # FIXME: use a list and join it instead,
    # too lazy to do it theis morning by myself
    content = ""

    print("\n\nUpdating events:")
    if events_list:
        for event in events_list:
            print(f"Event updated: {event['source']} → {event['name']}")
            # append instead of concat a string
            content += f"\n\n**{event['source']}** → {event['name']}"
        api.post_incident(
            slug="zbx2kuma",
            title="Current Incidents",
            content=content,
            style=IncidentStyle.WARNING,
        )
    else:
        print("No events!")
        api.unpin_incident(slug="zbx2kuma")
    api.disconnect()
