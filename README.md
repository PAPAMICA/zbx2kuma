<p align="center">
  <a href="https://papamica.com">
    <img src="https://img.papamica.com/logo/papamica.png" width="140px" alt="PAPAMICA" />
  </a>
</p>

<p align="center">
  <a href="#"><img src="https://readme-typing-svg.herokuapp.com?center=true&vCenter=true&lines=zbx2kuma;"></a>
</p>
<p align="center">
    Synchronize your Uptime Kuma with Zabbix events !
</p>
<p align="center">
    <a href="#"><img src="https://img.shields.io/badge/python-%233570A0.svg?style=for-the-badge&logo=python&logoColor=FFE05D"> </a>
    <a href="https://www.docker.com/"><img src="https://img.shields.io/badge/docker-%232496ED.svg?style=for-the-badge&logo=docker&logoColor=white"> </a>
    <a href="#"><img src="https://img.shields.io/badge/zabbix-%23CC2936.svg?style=for-the-badge&logo=Zotero&logoColor=white"> </a>
    <br />
</p>

# Presentation
This small script allows you to synchronize the status of Zabbix with Uptime Kuma.

It creates the different tags, monitors, a status page, and incidents dynamically.

Compatible with Zabix 6.x and Uptime Kuma 1.21.3.


# Configuration
## Credentials
Add the following environment variables:
```
ZABBIX_URL
ZABBIX_USERNAME
ZABBIX_PASSWORD
KUMA_URL
KUMA_USERNAME
KUMA_PASSWORD
```

## Zabbix
Supported version: 6.x

Create services directly in Zabbix, the script only accepts one level of parent:
 - Parent in Zabbix = Category in Uptime Kuma
 - Child in Zabbix = Monitor in Uptime Kuma

Remember to add the following tags to the children:
 - name = Monitor name (Example)
 - kuma.monitor = Monitor type (HTTP|PORT|PING)
 - HTTP: kuma.url = Monitor URL (https://example.papamica.com)
 - PORT/PING: kuma.hostname = Monitor hostname (example.papamica.com)
 - PORT: kuma.port = Monitor port
 
## Uptime Kuma
Supported version: 1.21.3

To avoid any conflict, install a new instance dedicated to zbx2kuma.
No other configuration is necessary.


# Use

## Docker
The simplest method is to deploy the script using Docker.

Clone repo :
```bash
git clone https://github.com/PAPAMICA/zbx2kuma.git
```
Build image :
```bash
cd zbx2kuma
docker build -t zbx2kuma .
```
Configure credentials and your network in `docker-compose.yml` :
```yaml
version : '3.4'

services:
  zbx2kuma:
    image: zbx2kuma
    container_name: zbx2kuma
    networks:
      - default
    environment:
      ZABBIX_URL: ''
      ZABBIX_USERNAME: ''
      ZABBIX_PASSWORD: ''
      KUMA_URL: ''
      KUMA_USERNAME: ''
      KUMA_PASSWORD: ''
    volumes:
    - /etc/localtime:/etc/localtime
networks:
  default:
    external:
      name: proxy
```
Create a cron job to run the script every 5 minutes:
```
*/5 * * * * docker-compose -f /path/to/docker-compose.yml up
```

## CLI
Export the following environment variables:
```bash
export ZABBIX_URL=""
export ZABBIX_USERNAME=""
export ZABBIX_PASSWORD=""
export KUMA_URL=""
export KUMA_USERNAME=""
export KUMA_PASSWORD=""
```
Run the script with python3:
```
python3 app.py
```