from interfaces.modbus.modbus import Modbus
from interfaces.mbus.mbus import Mbus
from models.meter_model import MeterModel
import threading
import logging

lock = threading.Lock()
log = logging.getLogger()


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class MeterManager(threading.Thread, metaclass=Singleton):
    meters = []

    def __init__(self):
        threading.Thread.__init__(self)
        threading.Thread.daemon = True
        self.threads = []

    def start(self) -> None:
        try:
            super(MeterManager, self).start()
        except RuntimeError:
            pass

    def run(self) -> None:
        log.debug("Meter Manager proces started")
        MeterModel.from_yaml("./data/meter.yaml")
        for meter_model in MeterModel.get_list().values():
            meter = None
            if meter_model.interface == "modbus":
                meter = Modbus.from_model(meter_model)
            if meter_model.interface == "mbus":
                meter = Mbus.from_model(meter_model)
            try:
                meter.start()
                self.threads.append(meter)
                MeterManager.meters.append(meter)
            except Exception as exception:
                log.exception(exception)
            else:
                log.debug(f"[Meter Manager] Meter created ({meter})")

    def get_meter_instance_by_address(self, address: int) -> object | None:
        for thread in self.threads:
            if thread.address == address:
                return thread
        return None

    def get_meter_by_host(self, host: str) -> object | None:
        for thread in self.threads:
            if thread.host == host:
                return thread
        return None

    def get_meter_by_host_and_address(self, host: str,
                                      address: int) -> object | None:
        for thread in self.threads:
            if thread.host == host and thread.address == address:
                return thread
        return None
