from test_base import TestBase


class TestMultipleInstallations(TestBase):

    def setup_class(self):
        self.installation_file_name = 'two_installations.json'
        self.ini_file_name = 'two_installations.ini'
        super().setup_class(self)


    def test_can_read_temperatures(self):
        actual = self.read_temperatures()
        assert len(actual) == 4, f'Expected 4 Temps (4 rooms, no HW, got {len(actual)}'


    def test_hot_water_temp_is_not_returned_for_a_location_without_hot_water(self):
        temperatures = self.read_temperatures()
        hot_water = [x for x in temperatures if x.zone == "Hot Water"]

        assert len(hot_water) == 0, f'Expected no Hot Water zone but found {len(hot_water)}'
