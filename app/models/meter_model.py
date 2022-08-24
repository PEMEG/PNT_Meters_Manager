import yaml
from yaml.loader import SafeLoader


class MeterModel:
    _list = {}

    @classmethod
    def from_yaml(cls, path: str) -> object:
        with open(path) as file:
            meters = yaml.load(file, Loader=SafeLoader)
        for meter in meters:
            meter_model = MeterModel.from_dict(meter)
            cls._list[meter_model.meter_id] = meter_model

    @classmethod
    def from_dict(cls, dictionary: dict) -> object:
        meter_id = dictionary['id']
        name = dictionary['name']
        host = dictionary['host']
        port = dictionary['port']
        address = dictionary['address']
        interface = dictionary['interface']
        return cls(meter_id=meter_id, name=name, host=host, port=port,
                   address=address, interface=interface)

    @classmethod
    def get_meter(cls, meter_id: int) -> object | None:
        try:
            meter = cls._list[meter_id]
        except:
            return None
        else:
            return meter

    @classmethod
    def get_list(cls) -> dict:
        return cls._list

    def __init__(self, meter_id: int, name: str, host: str, port: int,
                 address: int | None, interface: str) -> None:
        self._meter_id = meter_id
        self._name = name
        self._host = host
        self._port = port
        self._address = address
        self._interface = interface

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
    def address(self):
        return self._address

    @property
    def interface(self):
        return self._interface
