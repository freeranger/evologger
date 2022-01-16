from test_base import TestBase
from plugins.evohome import EvohomeMultiLocationClient

class TestEvoHomeMultiLocationClient(TestBase):

    def setup_class(self):
        self.installation_file_name = 'two_installations.json'
        self.ini_file_name = 'single_installation.ini'
        super().setup_class(self)
        self.client = EvohomeMultiLocationClient('testUser', 'testPassword', False)


    def test_get_location_returns_the_first_location_if_no_location_is_specified(self):

        actual = self.client.get_location()
        assert actual.locationId == '1', "Unexpected location Id"


    def test_get_location_returns_the_second_location_if_the_id_is_specified(self):
        actual = self.client.get_location('2')
        assert actual.locationId == '2', "Unexpected location Id"


    def test_get_location_returns_the_second_location_if_the_name_is_specified(self):
        actual = self.client.get_location('Dublin')
        assert actual.locationId == '2', "Unexpected location Id"
        assert actual.name == 'Dublin', "Unexpected location Name"


    def test_get_heating_system_returns_the_first_location_system_if_no_location_is_specified(self):
        actual = self.client.get_heating_system()
        assert actual.location.locationId == '1', "Unexpected location Id"


    def test_get_heating_system_returns_the_second_location_system_if_no_location_is_specified(self):
        actual = self.client.get_heating_system('2')
        assert actual.location.locationId == '2', "Unexpected location Id"


    def test_get_location_returns_the_second_location_if_the_name_is_specified(self):
        actual = self.client.get_heating_system('Dublin')
        assert actual.location.locationId == '2', "Unexpected location Id"
        assert actual.location.name == 'Dublin', "Unexpected location Name"
