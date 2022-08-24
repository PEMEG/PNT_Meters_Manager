from pyModbusTCP.client import ModbusClient
import struct
import logging
from . import constants as const

log = logging.getLogger()


def dec_to_bin(value) -> str:
    bin_val = f"{value:b}"
    bin_val = bin_val.zfill(16)
    return bin_val


def bin_to_double(value) -> float:
    hx = hex(int(value, 2))
    return struct.unpack("d", struct.pack("q", int(hx, 16)))[0]


def bin_to_float(binary) -> float:
    return struct.unpack('!f', struct.pack('!I', int(binary, 2)))[0]


class BaseFrame:
    def __init__(self, client: ModbusClient) -> None:
        self._client = client
        self._frame = None
        self._name = None
        self._register_offset = None
        self._register_range = None
        self._value = None

    @property
    def frame(self) -> str:
        return self._frame

    @property
    def name(self) -> str:
        return self._name

    @property
    def register_offset(self):
        return self._register_offset

    @property
    def register_range(self):
        return self._register_range

    @property
    def value(self) -> float:
        return self._value


class EnergyFrame(BaseFrame):
    def __init__(self, client: ModbusClient, tariff: int = 0,
                 phase: int = 0) -> None:
        super().__init__(client)
        self._tariff = tariff
        self._phase = phase

    @property
    def tariff(self) -> int:
        return self._tariff

    @property
    def phase(self) -> int:
        return self._phase

    @property
    def str_phase(self) -> str:
        match self._phase:
            case 0:
                return "total"
            case 1:
                return "phase_1"
            case 2:
                return "phase_2"
            case 3:
                return "phase_3"

    @property
    def str_tariff(self) -> str:
        match self._tariff:
            case 0:
                return "tariff_1"
            case 1:
                return "tariff_2"

    def export(self) -> dict:
        data = {
            "name": self._name,
            "phase": self.str_phase,
            "tariff": self.str_tariff,
            "value": self._value
        }
        return data

    def read_registers(self) -> None:
        reg_offset = self._register_offset
        reg_range = self._register_range
        if reg_offset is None or reg_range is None:
            self._value = None
            return
        regs = self._client.read_holding_registers(reg_offset, reg_range)
        bin_val = ""
        for x in range(len(regs)):
            bin_val += dec_to_bin(regs[x])
        self._value = bin_to_double(bin_val) / 1000


class ImportedActiveEnergyFrame(EnergyFrame):
    def __init__(self, client: ModbusClient, tariff: int = 0,
                 phase: int = 0) -> None:
        super().__init__(client, tariff, phase)
        self._name = "imported_active_energy"
        self._register_range = 4
        self._register_offset = self._get_offset()

    def _get_offset(self) -> int:
        tariff = self._tariff
        phase = self._phase
        offset = const.IMPORTED_ACTIVE_ENERGY[tariff][phase]
        return offset


class ActivePowerFrame(BaseFrame):
    def __init__(self, client: ModbusClient, phase: int = 0) -> None:
        super().__init__(client)
        self._name = "active_power"
        self._phase = phase
        self._register_range = 2
        self._register_offset = self._get_offset()

    @property
    def phase(self) -> int:
        return self._phase

    @property
    def str_phase(self) -> str:
        match self._phase:
            case 0:
                return "total"
            case 1:
                return "phase_1"
            case 2:
                return "phase_2"
            case 3:
                return "phase_3"

    def _get_offset(self) -> int:
        phase = self._phase
        offset = const.ACTIVE_POWER[phase]
        return offset

    def export(self) -> dict:
        data = {
            "name": self._name,
            "phase": self.str_phase,
            "value": self._value
        }
        return data

    def read_registers(self) -> None:
        reg_offset = self._register_offset
        reg_range = self._register_range
        if reg_offset is None or reg_range is None:
            self._value = None
            return
        regs = self._client.read_holding_registers(reg_offset, reg_range)
        bin_val = ""
        for x in range(len(regs)):
            bin_val += dec_to_bin(regs[x])
        self._value = bin_to_float(bin_val) / 1000
