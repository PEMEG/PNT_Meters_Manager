import os
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

INFLUXDB_URL = os.environ.get('INFLUXDB_URL')
INFLUXDB_TOKEN = os.environ.get('DOCKER_INFLUXDB_INIT_ADMIN_TOKEN')
INFLUXDB_ORG = os.environ.get('DOCKER_INFLUXDB_INIT_ORG')
INFLUXDB_BUCKET = os.environ.get('DOCKER_INFLUXDB_INIT_BUCKET')


class ActivePowerModel:
    def __init__(self, meter_id: int, active_power: float | None,
                 phase: int, date: datetime) -> None:
        self.meter_id = meter_id
        self.active_power = active_power
        self.phase = phase
        self.date = date

    def save(self) -> None:
        with InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN,
                            org=INFLUXDB_ORG) as client:
            write_api = client.write_api(write_options=SYNCHRONOUS)
            point = Point("active_power") \
                .tag("meter", f"meter{self.meter_id}") \
                .tag("phase", self.phase) \
                .field("active_power", self.active_power) \
                .time(self.date, WritePrecision.NS)
            write_api.write(INFLUXDB_BUCKET, INFLUXDB_ORG, point)
            client.close()
