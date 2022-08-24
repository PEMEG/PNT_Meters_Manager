from pyModbusTCP.client import ModbusClient
import threading
import time
import logging
from .modbus_frame import ImportedActiveEnergyFrame, ActivePowerFrame

log = logging.getLogger()


class Modbus(threading.Thread):
    def __init__(self, meter_id: int = 0, name: None | str = None,
                 host: str = 'localhost', port: int = 502):
        threading.Thread.__init__(self)
        threading.Thread.daemon = True
        self._client = None
        self._connected = False
        self._meter_id = meter_id
        self._name = name
        self._host = host
        self._port = port
        self._data = []

    @property
    def meter_id(self):
        return self._meter_id

    @property
    def name(self):
        return self._name

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def data(self):
        return self._data

    @classmethod
    def from_model(cls, model):
        return cls(meter_id=model.meter_id, name=model.name,
                   host=model.host, port=model.port)

    def run(self) -> None:
        while True:
            while not self._connected:
                self._connect()
                time.sleep(1)
            self._get_data()
            time.sleep(1)

    def _create_client(self) -> bool:
        try:
            self._client = ModbusClient()
            self._client.host(self._host)
            self._client.port(self._port)
            self._client.unit_id(1)
            # self._client.auto_open(True)
            self._client.timeout(3)
        except Exception as exception:
            log.exception(exception)
            return False
        else:
            log.debug(f"[meter_{self._meter_id}][Modbus] Client created")
            return True

    def _connect(self) -> bool:
        if self._client is None:
            if not self._create_client():
                self._connected = False
                return False
        if not self._client.is_open():
            if not self._client.open():
                self._connected = False
                return False
        log.debug(f"[meter_{self._meter_id}][Modbus] "
                  f"Connected to {self._host}:{self._port}")
        self._connected = True
        return True

    def _get_data(self):
        self._data = []
        imported_active_energy = ImportedActiveEnergyFrame(self._client)
        active_power = ActivePowerFrame(self._client)
        imported_active_energy.read_registers()
        active_power.read_registers()
        self._data.append(imported_active_energy.export())
        self._data.append(active_power.export())
