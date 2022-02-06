import pytest
from AppConfig import AppConfig
from test_base import TestBase, mock_data_file
from plugins.evohome import Plugin

class TestMultipleInstallations(TestBase):

    installation_file_name = 'two_installations.json'
    ini_file_name = 'two_installations.ini'

    def setup_class(self):
        super().setup_class(self)
        self.target = Plugin(AppConfig(mock_data_file(self.ini_file_name)))
        assert self.target._invalid_config is False

    @pytest.mark.unit
    def test_can_read_temperatures(self):
        actual = self.target.read()
        assert len(actual) == 4, f'Expected 4 Temps (4 rooms, no HW, got {len(actual)}'

    @pytest.mark.unit
    def test_hot_water_temp_is_not_returned_for_a_location_without_hot_water(self):
        temperatures = self.target.read()
        hot_water = [x for x in temperatures if x.zone == "Hot Water"]
        assert len(hot_water) == 0, f'Expected no Hot Water zone but found {len(hot_water)}'
