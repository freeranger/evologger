import unittest
from test_base import TestBase


class TestSingleInstallation(TestBase, unittest.TestCase):

    @property
    def installation_file_name(self):
        return 'single_installation.json'

    @property
    def ini_file_name(self):
        return 'single_installation.ini'

    def __init(self, installation_file_name):
        self.installation_file_name = installation_file_name

    def test_can_read_temperatures(self):
        actual = self.read_temperatures()
        self.assertEqual(len(actual), 6, "Expected 6 Temps (5 rooms + HW)")

    def test_hot_water_temp_is_returned_for_a_location_with_hot_water(self):
        temperatures = self.read_temperatures()
        hot_water = [x for x in temperatures if x.zone == "Hot Water"]

        self.assertEqual(len(hot_water), 1, 'Expected 1 Hot Water zone but found %s' % len(hot_water))

if __name__ == '__main__':
    unittest.main()

