from configparser import ConfigParser
import os
import json
import httpretty
import plugins.evohome as evohome


def mock_data_file(filename: str) -> str:
    return os.path.join(os.path.dirname(__file__), f'mock_data/{filename}')


# pylint: disable=W0201,W0212
class TestBase(object):

    installation_file_name = None
    ini_file_name = None

    def setup_class(self):
        with open(mock_data_file('account_info.json'), encoding='utf-8') as data_file:
            raw_account_info = data_file.read()
        self.account_info = json.loads(raw_account_info)

        with open(mock_data_file(self.installation_file_name), encoding='utf-8') as data_file:
            raw_installation_data = data_file.read()
        self.installation_info = json.loads(raw_installation_data)

        with open(mock_data_file('location_1_status.json'), encoding='utf-8') as data_file:
            raw_location_1_status = data_file.read()
        self.location_1_status = json.loads(raw_location_1_status)

        with open(mock_data_file('location_2_status.json'), encoding='utf-8') as data_file:
            raw_location_2_status = data_file.read()
        self.location_2_status = json.loads(raw_location_2_status)

        with open(mock_data_file('token.json'), encoding='utf-8') as data_file:
            self.token= data_file.read()

        httpretty.enable()
        httpretty.register_uri(httpretty.POST, "https://tccna.honeywell.com/Auth/OAuth/Token",
                               body=self.token,
                               content_type="application/json")
        httpretty.register_uri(httpretty.GET, "https://tccna.honeywell.com/WebAPI/emea/api/v1/userAccount",
                               body=raw_account_info,
                               content_type="application/json")
        httpretty.register_uri(httpretty.GET,
                               "https://tccna.honeywell.com/WebAPI/emea/api/v1/location/installationInfo?userId=%s&includeTemperatureControlSystems=True" %
                               self.account_info["userId"],
                               body=raw_installation_data,
                               content_type="application/json")
        httpretty.register_uri(httpretty.GET,
                               "https://tccna.honeywell.com/WebAPI/emea/api/v1/location/1/status?includeTemperatureControlSystems=True",
                               body=raw_location_1_status)

        httpretty.register_uri(httpretty.GET,
                              "https://tccna.honeywell.com/WebAPI/emea/api/v1/location/2/status?includeTemperatureControlSystems=True",
                              body=raw_location_2_status)

        config = ConfigParser(allow_no_value=True, inline_comment_prefixes=";")
        config.read(mock_data_file(self.ini_file_name))
        evohome._config = config
        section = evohome._config[evohome.plugin_name]
        evohome._hotwater = section['HotWater']
        if evohome._config.has_option(evohome.plugin_name,'Location'):
            evohome._location = evohome._config.get(evohome.plugin_name,'Location')
        else:
            evohome._location = None


    def teardown_class(self):
        httpretty.disable()  # disable afterwards, so that you will have no problems in code that uses that socket module
        httpretty.reset()


    def read_temperatures(self):
        """Reads the temps from the EvoHome module"""
        return evohome.read()
