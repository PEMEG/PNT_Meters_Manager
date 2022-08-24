import unittest
from unittest.mock import mock_open, patch, Mock, PropertyMock
from models.meter_model import MeterModel


class TestMeterModel(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        path = "./data/meter.yaml"
        content = """
---
- id: 1
  name: R1
  host: 192.168.33.212
  port: 502
  address:
  interface: modbus
- id: 2
  name: ECO
  host: 192.168.40.231
  port: 10001
  address: 7
  interface: mbus
                """
        mocked_file = mock_open(read_data=content)
        with patch("models.meter_model.open".format(__name__), mocked_file):
            MeterModel.from_yaml(path)
            cls.model_list = MeterModel.get_list()

    def test_load_from_yaml(self) -> None:
        for i in range(1, len(self.model_list)):
            expected = {
                1: MeterModel(1, "R1", "192.168.33.212", 502, None, "modbus"),
                2: MeterModel(2, "ECO", "192.168.40.231", 10001, 7, "mbus")
            }
            self.assertIsInstance(self.model_list[i], MeterModel)
            self.assertEqual(self.model_list[i].meter_id,
                             expected[i].meter_id)
            self.assertEqual(self.model_list[i].name, expected[i].name)
            self.assertEqual(self.model_list[i].host, expected[i].host)
            self.assertEqual(self.model_list[i].port, expected[i].port)
            self.assertEqual(self.model_list[i].address, expected[i].address)
            self.assertEqual(self.model_list[i].interface,
                             expected[i].interface)

    def test_get_meter(self) -> None:
        with patch("models.meter_model.MeterModel._list",
                   new_callable=PropertyMock) as model_list:
            model_list.return_value = self.model_list
            expected = MeterModel(1, "R1", "192.168.33.212",
                                  502, None, "modbus")
            actual = MeterModel.get_meter(1)
            self.assertEqual(actual.meter_id, expected.meter_id)
            self.assertEqual(actual.name, expected.name)
            self.assertEqual(actual.port, expected.port)
            self.assertEqual(actual.address, expected.address)
            self.assertEqual(actual.interface, expected.interface)


if __name__ == '__main__':
    unittest.main()
