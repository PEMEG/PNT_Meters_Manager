from . import constants as const
import logging

log = logging.getLogger()


def str_to_bytes(string: str) -> bytes:
    array = []
    final_str = ""
    while string:
        array.append(string[:2])
        string = string[2:]
    for i in array:
        final_str += str(i)
    return bytes.fromhex(final_str)


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


def bytes_to_str_list(data: bytes) -> list:
    """
    returns list of strings;
    index + 1 = byte position in doc
    """
    data_list = []
    for i in data:
        h = hex(i)
        data_list.append(f'{h[2:].zfill(2)}'.upper())
    return data_list


class ChecksumError(Exception):
    def __str__(self) -> str:
        return "The checksum is not correct"


class LengthFrameError(Exception):
    def __str__(self) -> str:
        return "The frame length does not match the L-field"


class LFieldRepetitionError(Exception):
    def __str__(self) -> str:
        return "L-field does not match the L-field repetition"


class MbusFrame:
    """
    Structure of Mbus frame (RSP_UD)

    byte: 1, size: 1, value(HEX): 68, description:
    Start character long telegram

    byte: 2, size: 1, value(HEX): xx, description:
    L-Field

    byte: 3, size: 1, value(HEX): xx, description:
    L-Field Repetition

    byte: 4, size: 1, value(HEX): 68, description:
    Start character long telegram repetition

    byte: 5, size 1, value(HEX): 08/18, description:
    C-Field RSP_UD

    byte: 6, size 1, value(HEX): xx, description:
    A-Field; Primary Address (00 - FA = 0 - 250)

    byte: 7, size: 1, value(HEX): 72, description:
    CI-Field

    byte 8-11, size 4, value(HEX): xx xx xx xx, description:
    M-BUS Interface Identification Number

    byte: 12-13, size 2, value(HEX): xx xx, description:
    Manufacturer's ID

    byte: 14, size: 1, value(HEX): xx, description:
    Version Number of M-BUS Interface Firmware (00 - FF)

    byte: 15, size: 1, value(HEX): 02, description:
    Medium - electricity

    byte: 16, size: 1, value(HEX): xx, description:
    Access Number (00 - FF > 00)

    byte: 17, size: 1, value(HEX): xx, description:
    M-BUS Interface Status

    byte: 18-19, size 2: value(HEX): 0000, description:
    Signature (always 0000)

    byte: 20-YY, size: 0-EA, value(HEX): xx...xx, description:
    Read-out Data Parameter

    byte: YY+1, size: 1, value(HEX): 0F/1F, description:
    DIF: 0F = no more data; 1F = other data to send

    byte: YY+2, size: 1, value(HEX): xx, description:
    CS Checksum; summed from C-Field to A Field included

    byte: YY+3, size: 1, value(HEX): 16, description:
    Stop character
    """

    def __init__(self, frame: bytes) -> None:
        self._frame = frame
        self._start_field = frame[:1]
        self._length_field = frame[1:2]
        self._length_field_rep = frame[2:3]
        self._start_field_rep = frame[3:4]
        self._control_field = frame[4:5]
        self._address_field = frame[5:6]
        self._data_field = frame[19:-3]
        self._checksum_field = frame[-2:-1]
        self._stop_field = frame[-1:]
        self._data = []
        self._address = int.from_bytes(self._address_field, "big")
        self._length = int.from_bytes(self._length_field, "big")
        self._full_length = len(frame)
        self._verify_length_repetition()
        self._verify_checksum()
        self._verify_frame_length()
        self._slice_data()

    @property
    def frame(self) -> bytes:
        return self._frame

    @property
    def start_field(self) -> bytes:
        return self._start_field

    @property
    def length_field(self) -> bytes:
        return self._length_field

    @property
    def length_field_rep(self) -> bytes:
        return self._length_field_rep

    @property
    def start_field_rep(self) -> bytes:
        return self._start_field_rep

    @property
    def control_field(self) -> bytes:
        return self._control_field

    @property
    def address_field(self) -> bytes:
        return self._address_field

    @property
    def data_field(self) -> bytes:
        return self._data_field

    @property
    def checksum_field(self) -> bytes:
        return self._checksum_field

    @property
    def stop_field(self) -> bytes:
        return self._stop_field

    @property
    def address(self) -> int:
        return self._address

    @property
    def data(self) -> list:
        return self._data

    @property
    def length(self) -> int:
        return self._length

    @property
    def full_length(self) -> int:
        return self._full_length

    def find_data(self, name: str = "", tariff: int = 0,
                  phase: int = 0) -> object | None:
        data = None
        for frame in self._data:
            found = []
            if hasattr(frame, 'name'):
                found.append(frame.name == name)
            if hasattr(frame, 'tariff'):
                found.append(frame.tariff == tariff)
            if hasattr(frame, 'phase'):
                found.append(frame.phase == phase)
            if found and all(found):
                return frame
        return None

    def export_data(self) -> list:
        data_list = []
        for frame in self._data:
            data_list.append(frame.export())
        return data_list

    def _slice_data(self) -> None:
        data_field = self._data_field
        data_list = bytes_to_str_list(data_field)
        while True:
            length = 0
            if data_list[0] == const.DIF6_E:
                if data_list[4] == const.IMPORTED_ENERGY:
                    length = ImportedActiveEnergyFrame.length()
                    data = data_field[:length]
                    frame = ImportedActiveEnergyFrame(data)
                    self._data.append(frame)
            if data_list[0] == const.DIF6:
                if data_list[1] == const.ACTIVE_POWER:
                    length = ActivePowerFrame.length()
                    data = data_field[:length]
                    frame = ActivePowerFrame(data)
                    self._data.append(frame)
            if len(data_field) - length > 0:
                data_field = data_field[length:]
                data_list = bytes_to_str_list(data_field)
            else:
                break

    def _verify_checksum(self) -> None:
        val = self._calculate_checksum()
        if self._checksum_field != val:
            raise ChecksumError

    def _verify_frame_length(self) -> None:
        length = int.from_bytes(self._length_field, "big") + 6
        if length != len(self._frame):
            raise LengthFrameError

    def _verify_length_repetition(self) -> None:
        if self._length_field != self._length_field_rep:
            raise LFieldRepetitionError

    def _calculate_checksum(self) -> bytes:
        sum_frame = self._frame[4:-2]
        int_val = 0
        for i in range(len(sum_frame)):
            int_val += int.from_bytes(sum_frame[i:i+1], "big")
        hex_val = hex(int_val)
        str_val = f'{hex_val[-2:].zfill(2)}'.upper()
        return str_to_bytes(str_val)


class EnergyFrame:
    """
    Structure of MBus data frame (Energy)

    byte: NN, size: 1, value(HEX): 86, description:
    DIF - 48 Bit Integer; 6 Byte; Followed by DIFE

    byte: NN+1, size: 1, value(HEX): x0, description:
    DIFE: 0 = Total; 1 = Tariff 1; 2 = Tariff 2

    byte: NN+2, size: 1, value(HEX): 82, description:
    VIF: Energy; Followed by VIFE

    byte: NN+3, size: 1, value(HEX): FF, description:
    VIFE: followed by MANUFACTURER specific VIFE

    byte: NN+4, size: 1, value(HEX): xx, description:
    VIFE; Followed by VIFE

    byte: NN+5, size: 1, value(HEX): FF, description:
    VIFE: followed by MANUFACTURER specific VIFE

    byte: NN+6, size: 1, value(HEX): 0x, description:
    Specific VIFE: 0 = 3-Phase; 1 = Phase 1; 2 = Phase 2; 3 = Phase 3

    byte: NN+7 - NN+12, size: 6, value(HEX): xx...xx, description:
    Value
    """

    def __init__(self, frame: bytes) -> None:
        self._frame = frame
        self._dif = frame[:1]
        self._dife = frame[1:2]
        self._vif = frame[2:3]
        self._vife = frame[4:5]
        self._spec_vife = frame[6:7]
        self._value_field = frame[7:]
        self._tariff = self._set_tariff()
        self._phase = self._set_phase()
        self._value = self._set_value()
        self._name = None

    @property
    def frame(self) -> bytes:
        return self._frame

    @property
    def dif(self) -> bytes:
        return self._dif

    @property
    def dife(self) -> bytes:
        return self._dife

    @property
    def vif(self) -> bytes:
        return self._vif

    @property
    def vife(self) -> bytes:
        return self._vife

    @property
    def spec_vife(self) -> bytes:
        return self._spec_vife

    @property
    def value_field(self) -> bytes:
        return self._value_field

    @property
    def tariff(self) -> int:
        return self._tariff

    @property
    def phase(self) -> int:
        return self._phase

    @property
    def value(self) -> float:
        return self._value

    @property
    def name(self) -> str:
        return self._name

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
                return "total"
            case 1:
                return "tariff_1"
            case 2:
                return "tariff_2"

    def _set_phase(self) -> int:
        val = bytes_to_str(self._spec_vife)
        match val[-1]:
            case "0":
                self._phase = 0
                return 0
            case "1":
                self._phase = 1
                return 1
            case "2":
                self._phase = 2
                return 2
            case "3":
                self._phase = 3
                return 3

    def _set_tariff(self) -> int:
        val = bytes_to_str(self._dife)
        if val in const.TOTAL:
            self._tariff = 0
            return 0
        if val in const.TARIFF1:
            self._tariff = 1
            return 1
        if val in const.TARIFF2:
            self._tariff = 2
            return 2

    def _set_value(self) -> float:
        int_val = int.from_bytes(self._value_field, "little")
        # kWh conversion
        final_val = int_val / 10000
        self._value = final_val
        return final_val

    def export(self) -> dict:
        data = {
            "name": self._name,
            "phase": self.str_phase,
            "tariff": self.str_tariff,
            "value": self._value
        }
        return data

    @staticmethod
    def length() -> int:
        """returns length of the frame"""
        return 13


class ImportedActiveEnergyFrame(EnergyFrame):
    """
    Structure of MBus data frame

    byte: NN, size: 1, value(HEX): 86, description:
    DIF - 48 Bit Integer; 6 Byte; Followed by DIFE

    byte: NN+1, size: 1, value(HEX): x0, description:
    DIFE: 0 = Total; 1 = Tariff 1; 2 = Tariff 2

    byte: NN+2, size: 1, value(HEX): 82, description:
    VIF: Energy; Followed by VIFE

    byte: NN+3, size: 1, value(HEX): FF, description:
    VIFE: followed by MANUFACTURER specific VIFE

    byte: NN+4, size: 1, value(HEX): 80, description:
    VIFE: Imported Energy; Followed by VIFE

    byte: NN+5, size: 1, value(HEX): FF, description:
    VIFE: followed by MANUFACTURER specific VIFE

    byte: NN+6, size: 1, value(HEX): 0x, description:
    Specific VIFE: 0 = 3-Phase; 1 = Phase 1; 2 = Phase 2; 3 = Phase 3

    byte: NN+7 - NN+12, size: 6, value(HEX): xx...xx, description:
    Value
    """

    def __init__(self, frame: bytes) -> None:
        super().__init__(frame)
        self._name = "imported_active_energy"


class ActivePowerFrame:
    """
    Structure of MBus data frame (Active Power)

    byte: NN, size: 1, value(HEX): 06, description:
    DIF - 48 Bit Integer; 6 Byte

    byte: NN+1, size: 1, value(HEX): A8, description:
    VIF: Active Power; Followed by VIFE

    byte: NN+2, size: 1, value(HEX): FF, description:
    VIFE: followed by MANUFACTURER specific VIFE

    byte: NN+3, size: 1, value(HEX): 0x, description:
    Specific VIFE: 0 = 3-Phase; 1 = Phase 1; 2 = Phase 2; 3 = Phase 3

    byte: NN+4 - NN+9, size: 6, value(HEX): xx...xx, description:
    Signed Value
    """

    def __init__(self, frame: bytes) -> None:
        self._frame = frame
        self._dif = frame[:1]
        self._vif = frame[1:2]
        self._spec_vife = frame[3:4]
        self._value_field = frame[4:]
        self._phase = self._set_phase()
        self._value = self._set_value()
        self._name = "active_power"

    @property
    def frame(self) -> bytes:
        return self._frame

    @property
    def dif(self) -> bytes:
        return self._dif

    @property
    def vif(self) -> bytes:
        return self._vif

    @property
    def spec_vife(self) -> bytes:
        return self._spec_vife

    @property
    def value_field(self) -> bytes:
        return self._value_field

    @property
    def phase(self) -> int:
        return self._phase

    @property
    def value(self) -> float:
        return self._value

    @property
    def name(self) -> str:
        return self._name

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

    def _set_phase(self) -> int:
        match bytes_to_str(self._spec_vife):
            case "00":
                self._phase = 0
                return 0
            case "01":
                self._phase = 1
                return 1
            case "02":
                self._phase = 2
                return 2
            case "03":
                self._phase = 3
                return 3

    def _set_value(self) -> float:
        int_val = abs(int.from_bytes(self._value_field,
                                     "little", signed=True))
        watts_val = int_val / 1000
        kilowatts_val = watts_val / 1000
        self._value = kilowatts_val
        return kilowatts_val

    def export(self) -> dict:
        data = {
            "name": self._name,
            "phase": self.str_phase,
            "value": self._value
        }
        return data

    @staticmethod
    def length() -> int:
        """returns length of the frame"""
        return 10


class _ShortTelegram:
    """
    SND_NKE structure

    byte: 1, size: 1, value(HEX): 10, description:
    Start character - short telegram

    byte: 2, size: 1, value(HEX): xx, description:
    C Field

    byte: 3, size 1, value(HEX): xx, description:
    A Field - Primary Address (00 - FA)

    byte: 4, size: 1, value(HEX): xx, description:
    CS Checksum; Summed from C-Field to A-Field included

    byte: 5, size: 1, value(HEX): 16, description:
    Stop character
    """

    def __init__(self, address: int = 1) -> None:
        self._frame = None
        self._start_field = "10"
        self._control_field = None
        self._address_field = None
        self._checksum_field = None
        self._stop_field = "16"
        self._address = address
        self._set_address_field()

    @property
    def frame(self) -> bytes:
        self._set_address_field()
        str_frame = ""
        str_frame += self._start_field
        str_frame += self._control_field
        str_frame += self._address_field
        str_frame += self._checksum_field
        str_frame += self._stop_field
        return str_to_bytes(str_frame)

    @property
    def start_field(self) -> str:
        return self._start_field

    @property
    def control_field(self) -> str:
        return self._control_field

    @property
    def address_field(self) -> str:
        return self._address_field

    @property
    def checksum_field(self) -> str:
        self._checksum_field = self._calculate_checksum()
        return self._checksum_field

    @property
    def stop_field(self) -> str:
        return self._stop_field

    @property
    def address(self) -> int:
        return self._address

    def _set_address_field(self) -> None:
        hex_val = hex(self._address)
        self._address_field = f'{hex_val[2:].zfill(2)}'.upper()
        self._checksum_field = self._calculate_checksum()

    def _calculate_checksum(self) -> str:
        if (self._address_field is not None and
                self._control_field is not None):
            int_control = int(self._control_field, 16)
            int_address = int(self._address_field, 16)
            int_checksum = int_control + int_address
            hex_checksum = hex(int_checksum)
            str_checksum = f'{hex_checksum[2:].zfill(2)}'.upper()
            return str_checksum


class SendInitFrame(_ShortTelegram):
    """
    SND_NKE structure

    byte: 1, size: 1, value(HEX): 10, description:
    Start character - short telegram

    byte: 2, size: 1, value(HEX): 40, description:
    C Field

    byte: 3, size 1, value(HEX): xx, description:
    A Field - Primary Address (00 - FA)

    byte: 4, size: 1, value(HEX): xx, description:
    CS Checksum; Summed from C-Field to A-Field included

    byte: 5, size: 1, value(HEX): 16, description:
    Stop character
    """

    def __init__(self, address: int = 1) -> None:
        super().__init__(address)
        self._control_field = "40"


class RequestUserData2Frame(_ShortTelegram):
    """
    REQ_UD2 structure

    byte: 1, size: 1, value(HEX): 10, description:
    Start character - short telegram

    byte: 2, size: 1, value(HEX): 7B/5B, description:
    C-Field; Transmit Read-Out Data

    byte: 3, size: 1, value(HEX): xx, description:
    A-Field - Primary Address

    byte: 4, size: 1, value(HEX): xx, description:
    CS Checksum; Summed from C-Field to A-Field included

    byte: 5, size: 1, value(HEX): 16, description:
    Stop character
    """

    def __init__(self, address: int = 1) -> None:
        super().__init__(address)
        self._control_field = "7B"
