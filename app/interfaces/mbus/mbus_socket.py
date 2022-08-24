import socket
import threading
import time
import logging
from .mbus_frame import MbusFrame

log = logging.getLogger()

def bytes_to_str(data: bytes) -> str:
    string = ""
    if len(data) < 2:
        h = hex(data[0])
        string += f'{h[2:].zfill(2)}'.upper()
        return string
    for i in data:
        h = hex(i)
        string += f'{h[2:].zfill(2)} '.upper()
    return string


class QuasiSingleton(type):
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, host: str, port: int):
        key = f"{host}:{port}"
        if key not in cls._instances:
            with cls._lock:
                if key not in cls._instances:
                    inst = super().__call__(host, port)
                    cls._instances[key] = inst
                    return inst
        return cls._instances[key]


class MbusSocket(threading.Thread, metaclass=QuasiSingleton):
    _socket_instances = []

    @classmethod
    def exists(cls, host: str, port: int) -> bool:
        for inst in cls._instances:
            if inst.host == host and inst.port == port:
                return True
        return False

    @classmethod
    def get_instances(cls) -> object:
        return cls._socket_instances

    def __init__(self, host: str = 'localhost', port: int = 10001) -> None:
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._meters = []
        self._connected = False
        self._buffer = b""
        self.host = host
        self.port = port
        threading.Thread.__init__(self)
        threading.Thread.daemon = True
        MbusSocket._socket_instances.append(self)
        log.debug(f"[Mbus Socket] Socket created ({self})")

    def __str__(self) -> str:
        return f"MbusSocket({self.host}:{self.port})"

    def connect(self) -> None:
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((self.host, self.port))
        except Exception as exception:
            log.debug(exception)
            log.error(f"[Mbus] Socket can't connect to "
                      f"{self.host}:{self.port}")
        else:
            self._socket.settimeout(5)
            self._connected = True
            log.debug(f"[Mbus] Socket connected to {self.host}:{self.port}")

    def close(self) -> None:
        try:
            self._socket.close()
        except Exception as exception:
            log.exception(exception)
        else:
            self._connected = False

    def receive(self) -> None:
        try:
            data = self.recv(1024)
        except socket.timeout:
            log.warning(f"[Mbus] Request timed out ({self.host}:{self.port})")
            pass
        else:
            self._buffer += data

    def recv(self, bufsize: int | None) -> bytes:
        return self._socket.recv(bufsize)

    def send(self, data: bytes | bytearray) -> int:
        return self._socket.send(data)

    def _update_meters_data(self) -> None:
        if not self._buffer:
            return
        slicer = _DataSlicer(self._buffer)
        for frame in slicer.frames:
            meter = self.get_meter(frame.address)
            if meter is None:
                continue
            meter.data = frame.export_data()
        log.debug(f"[MbusSocket._buffer] {bytes_to_str(self._buffer)}")
        self._buffer = b""

    def append(self, meter: object) -> None:
        self._meters.append(meter)

    def get_meter(self, address: int) -> object | None:
        for meter in self._meters:
            if meter.address == address:
                return meter
        return None

    def start(self):
        try:
            super(MbusSocket, self).start()
        except RuntimeError:
            pass

    def run(self):
        while True:
            while not self._connected:
                self.connect()
                time.sleep(1)
            for meter in self._meters:
                meter.send_commands()
                time.sleep(1)
                self.receive()
                time.sleep(1)
            self._update_meters_data()
            time.sleep(30)


class _DataSlicer:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self._frames = self._find_frames()

    @property
    def frames(self):
        if self._frames:
            return self._frames
        else:
            self._find_frames()

    def _find_frames(self):
        frames = []
        for i in range(len(self.data)):
            if i + 1 > len(self.data):
                break
            str_val = bytes_to_str(self.data[i:i+1])
            if str_val != "68":
                continue
            if self.data[i+1:i+2] != self.data[i+2:i+3]:
                continue
            length = int.from_bytes(self.data[i+1:i+2], "big") + 6
            frame = MbusFrame(self.data[i:i+length])
            frames.append(frame)
            self.data = self.data[length:]
            log.debug(f"[MbusSocket._find_frames]: {bytes_to_str(self.data)}")
        return frames
