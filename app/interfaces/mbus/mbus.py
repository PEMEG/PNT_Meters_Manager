import time
from .mbus_socket import MbusSocket
from .mbus_frame import SendInitFrame, RequestUserData2Frame


class Mbus:
    _instances = []

    def __init__(self, meter_id: int = 0, name: None | str = None,
                 host: str = 'localhost', port: int = 10001,
                 address: int = 1):
        self._socket = MbusSocket(host, port)
        self.meter_id = meter_id
        self.name = name
        self.host = host
        self.port = port
        self.address = address
        self.data = None
        Mbus._instances.append(self)
        self._socket.append(self)

    def __new__(cls, meter_id: int, name: str, host: str, port: int,
                address: int) -> object:
        for inst in cls._instances:
            found = [inst.meter_id == meter_id,
                     inst.host == host,
                     inst.port == port,
                     inst.address == address]
            if all(found):
                return inst
        return object.__new__(Mbus)

    def __str__(self) -> str:
        return f"Mbus({self.host}:{self.port} [{self.address}])"

    def __repr__(self) -> str:
        return f"Mbus({self.host}:{self.port} [{self.address}])"

    @classmethod
    def from_model(cls, model):
        return cls(meter_id=model.meter_id, name=model.name, host=model.host,
                   port=model.port, address=model.address)

    @property
    def socket(self):
        return self._socket

    def send(self, msg) -> None:
        self._socket.send(msg)

    def send_commands(self) -> None:
        init_frame = SendInitFrame(self.address)
        req_data_frame = RequestUserData2Frame(self.address)
        self.send(init_frame.frame)
        time.sleep(0.5)
        self.send(req_data_frame.frame)
        time.sleep(0.5)

    def start(self) -> None:
        self._socket.start()
