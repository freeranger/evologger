import unittest
from test_base import TestBase


class TestMultipleInstallations(TestBase, unittest.TestCase):

    @property
    def installation_file_name(self):
        return 'two_installations.json'

    @property
    def ini_file_name(self):
        return 'two_installations.ini'

    def __init(self, installation_file_name):
        self.installation_file_name = installation_file_name

    def test_can_read_temperatures(self):
        actual = self.read_temperatures()
        self.assertEqual(len(actual), 4, "Expected 4 Temps (4 rooms, no HW), got %s" % len(actual))

    def test_hot_water_temp_is_not_returned_for_a_location_without_hot_water(self):
        temperatures = self.read_temperatures()
        hot_water = [x for x in temperatures if x.zone == "Hot Water"]

        self.assertEqual(len(hot_water), 0, 'Expected no Hot Water zone but found %s' % len(hot_water))


if __name__ == '__main__':
    unittest.main()

