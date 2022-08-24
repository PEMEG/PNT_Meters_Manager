import os
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

INFLUXDB_URL = os.environ.get('INFLUXDB_URL')
INFLUXDB_TOKEN = os.environ.get('DOCKER_INFLUXDB_INIT_ADMIN_TOKEN')
INFLUXDB_ORG = os.environ.get('DOCKER_INFLUXDB_INIT_ORG')
INFLUXDB_BUCKET = os.environ.get('DOCKER_INFLUXDB_INIT_BUCKET')


class ImportedActiveEnergyModel:
    def __init__(self, meter_id: int, imported_active_energy: float | None,
                 tariff: int, phase: int, date: datetime) -> None:
        self.meter_id = meter_id
        self.imported_active_energy = imported_active_energy
        self.tariff = tariff
        self.phase = phase
        self.date = date

    def save(self) -> None:
        with InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN,
                            org=INFLUXDB_ORG) as client:
            write_api = client.write_api(write_options=SYNCHRONOUS)
            point = Point("imported_active_energy") \
                .tag("meter", f"meter{self.meter_id}") \
                .tag("tariff", self.tariff) \
                .tag("phase", self.phase) \
                .field("imported_active_energy", self.imported_active_energy) \
                .time(self.date, WritePrecision.NS)
            write_api.write(INFLUXDB_BUCKET, INFLUXDB_ORG, point)
            client.close()
