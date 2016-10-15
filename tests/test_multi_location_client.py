import unittest
from mock import patch
from test_base import TestBase


class TestEvoHomeMultiLocationClient(TestBase, unittest.TestCase):

    @property
    def installation_file_name(self):
        return 'two_installations.json'

    @property
    def ini_file_name(self):
        return 'single_installation.ini'

    def __init(self, installation_file_name):
        self.installation_file_name = installation_file_name

    def setUp(self):
        super(TestEvoHomeMultiLocationClient, self).setUp()

        with patch('ConfigParser.open', create=True) as open_:
            with open('mock_data/' + self.ini_file_name) as file_:
                def reset():
                    file_.seek(0)

                open_.return_value.readline = file_.readline
                open_.return_value.close = reset

                from evohome import EvohomeMultiLocationClient

                self.client = EvohomeMultiLocationClient('testUser', 'testPassword', False)

    def test_get_location_returns_the_first_location_if_no_location_is_specified(self):

        actual = self.client.get_location()
        self.assertEqual(actual.locationId, '1', "Unexpected location Id")


    def test_get_location_returns_the_second_location_if_the_id_is_specified(self):
        actual = self.client.get_location('2')
        self.assertEqual(actual.locationId, '2', "Unexpected location Id")

    def test_get_location_returns_the_second_location_if_the_name_is_specified(self):
        actual = self.client.get_location('Dublin')
        self.assertEqual(actual.locationId, '2', "Unexpected location Id")
        self.assertEqual(actual.name, 'Dublin', "Unexpected location Name")

    def test_get_heating_system_returns_the_first_location_system_if_no_location_is_specified(self):
        actual = self.client.get_heating_system()
        self.assertEqual(actual.location.locationId, '1', "Unexpected location Id")


    def test_get_heating_system_returns_the_second_location_system_if_no_location_is_specified(self):
        actual = self.client.get_heating_system('2')
        self.assertEqual(actual.location.locationId, '2', "Unexpected location Id")


    def test_get_location_returns_the_second_location_if_the_name_is_specified(self):
        actual = self.client.get_heating_system('Dublin')
        self.assertEqual(actual.location.locationId, '2', "Unexpected location Id")
        self.assertEqual(actual.location.name, 'Dublin', "Unexpected location Name")



if __name__ == '__main__':
    unittest.main()
