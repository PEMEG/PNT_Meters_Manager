from meter_manager import MeterManager
import time
import threading
from datetime import datetime, timedelta
from models.active_power_model import ActivePowerModel
from models.imported_active_energy_model import ImportedActiveEnergyModel
import logging

lock = threading.Lock()
log = logging.getLogger()


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super(Singleton, cls)\
                        .__call__(*args, **kwargs)
        return cls._instances[cls]


class DatabaseScheduler(threading.Thread, metaclass=Singleton):
    def __init__(self) -> None:
        threading.Thread.__init__(self)
        threading.Thread.daemon = True
        self.meter_manager = MeterManager()
        self.meter_manager.start()
        self._last_date = None

    def _round_date(self, date) -> datetime:
        new_date = date
        new_date = new_date.replace(microsecond=0)
        new_date = new_date - timedelta(seconds=date.second % 60)
        return new_date

    def start(self) -> None:
        try:
            super(DatabaseScheduler, self).start()
        except RuntimeError:
            pass

    def run(self) -> None:
        log.debug("Database Scheduler process started")
        self._last_date = self._round_date(datetime.now())
        while True:
            if self._last_date + timedelta(seconds=60) <= datetime.now():
                self._last_date += timedelta(seconds=60)
                self._save_meters_data()
            time.sleep(.5)

    def _save_meters_data(self) -> None:
        log.info("[Database Scheduler] Saving meters data")
        for meter in self.meter_manager.threads:
            if not meter.data:
                log.info(LogFormatter(None, meter))
                continue
            for measurement in meter.data:
                if measurement["name"] == "imported_active_energy":
                    model = ImportedActiveEnergyModel(
                        meter_id=meter.meter_id,
                        imported_active_energy=measurement["value"],
                        tariff=measurement["tariff"],
                        phase=measurement["phase"],
                        date=self._last_date)
                    model.save()
                    log.info(LogFormatter(measurement, meter))
                if measurement["name"] == "active_power":
                    model = ActivePowerModel(
                        meter_id=meter.meter_id,
                        active_power=measurement["value"],
                        phase=measurement["phase"],
                        date=self._last_date)
                    model.save()
                    log.info(LogFormatter(measurement, meter))


class LogFormatter:
    _max_length = 0

    def __init__(self, dic: dict | None, meter: object) -> None:
        self._check_length()
        self._dict = dic
        self._name = meter.name
        self._id = meter.meter_id
        self._id_phrase = f"[meter_{self._id}]"
        self._name_phrase = f"{self._name}"
        self._log = ""

    def __str__(self) -> str:
        if self._log == "":
            self._form_log()
        return self._log

    def __repr__(self) -> str:
        if self._log == "":
            self._form_log()
        return self._log

    def _check_length(self) -> None:
        if LogFormatter._max_length > 0:
            return
        for meter in MeterManager.meters:
            if LogFormatter._max_length < len(meter.name):
                LogFormatter._max_length = len(meter.name)

    def _form_log(self) -> None:
        self._log = f"{self._id_phrase: <10} " \
                    f"{self._name_phrase: <{LogFormatter._max_length}} | "
        if self._dict is None:
            self._log += "None"
            return
        self._log += f"{self._dict['name']}: {self._dict['value']} "
        for k, v in self._dict.items():
            if k == "value" or k == "name":
                continue
            self._log += f"({k}: {v}) "
