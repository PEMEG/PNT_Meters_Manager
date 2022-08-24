import unittest
from interfaces.mbus.mbus_frame import MbusFrame, str_to_bytes, \
    ChecksumError, LengthFrameError, LFieldRepetitionError, \
    EnergyFrame, ActivePowerFrame


class TestMbusFrame(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.raw_frame = "68 45 45 68 08 07 72 57 28 01 00 87 05 04 02 10 " \
                        "00 00 00 06 A8 FF 01 00 00 00 00 00 00 06 A8 FF " \
                        "02 4D 90 02 00 00 00 06 A8 FF 03 00 00 00 00 00 " \
                        "00 06 A8 FF 00 4D 90 02 00 00 00 86 00 82 FF 80 " \
                        "FF 00 A8 ED B1 03 00 00 0F F9 16"
        cls.mbus_frame = MbusFrame(str_to_bytes(cls.raw_frame))
        cls.energy_frame = EnergyFrame(str_to_bytes("86 00 82 FF 80 FF 00 "
                                                    "A8 ED B1 03 00 00"))
        cls.active_power_frame = ActivePowerFrame(
            str_to_bytes("06 A8 FF 02 4D 90 02 00 00 00")
        )

    def test_bytes_mapping(self) -> None:
        self.assertEqual(self.mbus_frame.start_field, str_to_bytes("68"))
        self.assertEqual(self.mbus_frame.length_field, str_to_bytes("45"))
        self.assertEqual(self.mbus_frame.length_field_rep, str_to_bytes("45"))
        self.assertEqual(self.mbus_frame.start_field_rep, str_to_bytes("68"))
        self.assertEqual(self.mbus_frame.control_field, str_to_bytes("08"))
        self.assertEqual(self.mbus_frame.address_field, str_to_bytes("07"))
        self.assertEqual(self.mbus_frame.data_field,
                         str_to_bytes("06 A8 FF 01 00 00 00 00 00 00 06 A8 FF "
                                      "02 4D 90 02 00 00 00 06 A8 FF 03 00 00 "
                                      "00 00 00 00 06 A8 FF 00 4D 90 02 00 00 "
                                      "00 86 00 82 FF 80 FF 00 A8 ED B1 03 00 "
                                      "00"))
        self.assertEqual(self.mbus_frame.checksum_field, str_to_bytes("F9"))
        self.assertEqual(self.mbus_frame.stop_field, str_to_bytes("16"))

    def test_address_conversion(self) -> None:
        self.assertEqual(self.mbus_frame.address, 7)

    def test_length_conversion(self) -> None:
        self.assertEqual(self.mbus_frame.length, 69)

    def test_full_length_conversion(self) -> None:
        self.assertEqual(self.mbus_frame.full_length, 75)

    def test_checksum_verification_with_wrong_data(self) -> None:
        raw_frame = "68 45 45 68 08 07 72 57 28 01 00 87 05 04 02 10 " \
                    "00 00 00 06 A8 FF 01 00 00 00 00 00 00 06 A8 FF " \
                    "02 4D 90 02 00 00 00 06 A8 FF 03 00 00 00 00 00 " \
                    "00 06 A8 FF 00 4D 90 02 10 00 00 86 00 82 FF 80 " \
                    "FF 00 A8 ED B1 03 00 00 0F F9 16"
        with self.assertRaises(ChecksumError):
            MbusFrame(str_to_bytes(raw_frame))

    def test_length_verification_with_too_short_frame(self) -> None:
        raw_frame = "68 45 45 68 08 07 72 57 28 01 00 87 05 04 02 10 " \
                    "00 00 00 06 A8 FF 01 00 00 00 00 00 00 06 A8 FF " \
                    "02 4D 90 02 00 00 00 06 A8 FF 03 00 00 00 00 00 " \
                    "00 06 A8 FF 00 4D 90 02 00 00 86 00 82 FF 80 " \
                    "FF 00 A8 ED B1 03 00 00 0F F9 16 "
        with self.assertRaises(LengthFrameError):
            MbusFrame(str_to_bytes(raw_frame))

    def test_length_verification_with_too_long_frame(self) -> None:
        raw_frame = "68 45 45 68 08 07 72 57 28 01 00 87 05 04 02 10 " \
                    "00 00 00 06 A8 FF 01 00 00 00 00 00 00 06 A8 FF " \
                    "02 4D 90 02 00 00 00 06 A8 FF 03 00 00 00 00 00 " \
                    "00 06 A8 FF 00 4D 90 02 00 00 00 86 00 82 FF 80 " \
                    "FF 00 A8 ED B1 03 00 00 0F F9 16 00"
        with self.assertRaises(ChecksumError):
            MbusFrame(str_to_bytes(raw_frame))

    def test_length_repetition_matching(self) -> None:
        raw_frame = "68 45 25 68 08 07 72 57 28 01 00 87 05 04 02 10 " \
                    "00 00 00 06 A8 FF 01 00 00 00 00 00 00 06 A8 FF " \
                    "02 4D 90 02 00 00 00 06 A8 FF 03 00 00 00 00 00 " \
                    "00 06 A8 FF 00 4D 90 02 00 00 00 86 00 82 FF 80 " \
                    "FF 00 A8 ED B1 03 00 00 0F F9 16"
        with self.assertRaises(LFieldRepetitionError):
            MbusFrame(str_to_bytes(raw_frame))

    def test_slice_data(self) -> None:
        frame_list = [
            str_to_bytes("06 A8 FF 01 00 00 00 00 00 00"),
            str_to_bytes("06 A8 FF 02 4D 90 02 00 00 00"),
            str_to_bytes("06 A8 FF 03 00 00 00 00 00 00"),
            str_to_bytes("06 A8 FF 00 4D 90 02 00 00 00"),
            str_to_bytes("86 00 82 FF 80 FF 00 A8 ED B1 03 00 00")
        ]
        tested_list = []
        for frame in self.mbus_frame.data:
            tested_list.append(frame.frame)
        self.assertCountEqual(tested_list, frame_list)

    def test_energy_frame_set_value(self) -> None:
        self.assertEqual(self.energy_frame.value, 6199.236)

    def test_energy_frame_set_tariff(self) -> None:
        self.assertEqual(self.energy_frame.tariff, 0)

    def test_energy_frame_str_tariff(self) -> None:
        self.assertEqual(self.energy_frame.str_tariff, "total")

    def test_energy_frame_set_phase(self) -> None:
        self.assertEqual(self.energy_frame.phase, 0)

    def test_energy_frame_str_phase(self) -> None:
        self.assertEqual(self.energy_frame.str_phase, "total")

    def test_energy_frame_length(self) -> None:
        self.assertEqual(self.energy_frame.length(), 13)

    def test_energy_frame_export(self) -> None:
        standard_dict = {
            "name": None,
            "phase": "total",
            "tariff": "total",
            "value": 6199.236
        }
        self.assertEqual(self.energy_frame.export(), standard_dict)

    def test_active_power_frame_set_value(self) -> None:
        self.assertEqual(self.active_power_frame.value, 0.168013)

    def test_active_power_frame_set_phase(self) -> None:
        self.assertEqual(self.active_power_frame.phase, 2)

    def test_active_power_frame_str_phase(self) -> None:
        self.assertEqual(self.active_power_frame.str_phase, "phase_2")

    def test_active_power_frame_length(self) -> None:
        self.assertEqual(self.active_power_frame.length(), 10)

    def test_active_power_frame_export(self) -> None:
        standard_dict = {
            "name": "active_power",
            "phase": "phase_2",
            "value": 0.168013
        }
        self.assertEqual(self.active_power_frame.export(), standard_dict)


if __name__ == '__main__':
    unittest.main()
