import os
import json
import httpretty
from AppConfig import AppConfig
import plugins.evohome as evohome

def mock_data_file(filename: str) -> str:
    return os.path.join(os.path.dirname(__file__), f'mock_data/{filename}')


class TestBase(object):

    ini_file_name: str = None
    installation_file_name: str = None

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

    def tearDown(self):
        httpretty.disable()  # disable afterwards, so that you will have no problems in code that uses that socket module
        httpretty.reset()
