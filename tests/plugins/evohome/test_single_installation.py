import pytest
from AppConfig import AppConfig
from test_base import TestBase, mock_data_file
from plugins.evohome import Plugin

class TestSingleInstallation(TestBase):

    installation_file_name = 'single_installation.json'
    ini_file_name = 'single_installation.ini'

    def setup_class(self):
        super().setup_class(self)
        self.target = Plugin(AppConfig(mock_data_file(self.ini_file_name)))
        assert self.target._invalid_config is False

    def test_can_read_temperatures(self):
        actual = self.target.read()
        assert len(actual) == 6, 'Expected 6 Temps (5 rooms + HW)'

    def test_hot_water_temp_is_returned_for_a_location_with_hot_water(self):
        temperatures = self.target.read()
        hot_water = [x for x in temperatures if x.zone == "Hot Water"]

        assert len(hot_water) == 1, 'Expected 1 Hot Water zone but found %s' % len(hot_water)
