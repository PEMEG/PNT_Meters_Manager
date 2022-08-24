# PNT Meters Manager
The application was created for Science and Technology Park in Opole. The main goal of the project was to collect and present data from electric meters.

Communication with meters takes place via mbus and modbus interfaces. The data is stored in the MariaDB and [InfluxDB](https://www.influxdata.com/) databases. The collector was created in python, while as the visualizer was used grafana.

## Table of contents
* [Technologies](#technologies)
* [Devices](#devices)
* [Setup](#setup)
* [Usage](#usage)
* [Credits](#credits)

## Technologies
- Python
- Grafana
- MariaDB
- InfluxDB

## Devices
- Modbus electric meter - Siemens PAC2200
- Mbus electric meter - Algodue UEM1P5-D
- Mbus-Ethernet converter - ADFweb HD67030-B2-20

## Setup
To run the app will be needed:
- Docker
- Docker-composer
- MariaDB

Build project:
```bash
docker-compose build
```

Run:
```bash
docker-compose up -d
```

## Usage
The configuration data of the meters are stored in YAML file (_app/data/meter.yaml_). The collector is adapted to direct connection with the modbus meters, while the connection to the mbus meters is via mbus-ethernet converter. The address is valid only in the case of mbus and means the internal address of the converter.

Example configuration:

```yaml
# app/data/meter.yaml
- id: 1
  name: modbus_meter
  host: 192.168.1.10
  port: 502
  address:
  interface: modbus
- id: 2
  name: mbus_meter
  host: 192.168.1.11
  port: 10001
  address: 3
  interface: mbus
```

## Credits
![Park Naukowo-Technologiczny w Opolu](https://pnt.opole.pl/templates/test_dobry2/images/designer/0f1d1217fca330398a650c1320a5eff9_logo.png)