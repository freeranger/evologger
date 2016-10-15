import json
import httpretty
from mock import patch

import context  # need this line in so evohome etc can be found

class TestBase(object):

    @property
    def installation_file_name(self):
        return None

    def setUp(self):
        with open('mock_data/account_info.json') as data_file:
            raw_account_info = data_file.read()
        self.account_info = json.loads(raw_account_info)

        with open('mock_data/' + self.installation_file_name) as data_file:
            raw_installation_data = data_file.read()
        self.installation_info = json.loads(raw_installation_data)

        with open('mock_data/location_1_status.json') as data_file:
            raw_location_1_status = data_file.read()
        self.location_1_status = json.loads(raw_location_1_status)

        with open('mock_data/location_2_status.json') as data_file:
            raw_location_2_status = data_file.read()
        self.location_2_status = json.loads(raw_location_2_status)

        httpretty.enable()
        httpretty.register_uri(httpretty.POST, "https://tccna.honeywell.com/Auth/OAuth/Token",
                               body='{"access_token": "TEST_TOKEN"}',
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


    def read_temperatures(self):
        with patch('ConfigParser.open', create=True) as open_:
            with open('mock_data/' + self.ini_file_name) as file_:
                def reset():
                    file_.seek(0)

                open_.return_value.readline = file_.readline
                open_.return_value.close = reset

                import evohome
                return evohome.read()