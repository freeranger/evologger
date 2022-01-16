from test_base import TestBase


class TestSingleInstallation(TestBase):

    def setup_class(self):
        self.installation_file_name = 'single_installation.json'
        self.ini_file_name = 'single_installation.ini'
        super().setup_class(self)


    def test_can_read_temperatures(self):
        actual = self.read_temperatures()
        assert len(actual) == 6, 'Expected 6 Temps (5 rooms + HW)'


    def test_hot_water_temp_is_returned_for_a_location_with_hot_water(self):
        temperatures = self.read_temperatures()
        hot_water = [x for x in temperatures if x.zone == "Hot Water"]

        assert len(hot_water) == 1, 'Expected 1 Hot Water zone but found %s' % len(hot_water)



