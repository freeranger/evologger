import httpretty
import json
import pytest
from AppConfig import AppConfig
from test_base import mock_data_file
from plugins.evohome import Plugin

_installation_file_name = mock_data_file('single_installation.json')
_ini_file_name = mock_data_file('single_installation.ini')

with open(mock_data_file('account_info.json'), encoding='utf-8') as data_file:
    raw_account_info = data_file.read()
_account_info = json.loads(raw_account_info)

with open(_installation_file_name, encoding='utf-8') as data_file:
    raw_installation_data = data_file.read()
_installation_info = json.loads(raw_installation_data)

@pytest.fixture
def target():

    httpretty.enable()
    yield Plugin(AppConfig(_ini_file_name))
    httpretty.disable()  # disable afterwards, so that you will have no problems in code that uses that socket module
    httpretty.reset()

@pytest.mark.unit
@pytest.mark.parametrize('status', [ 400, 429, 500, 503 ])
def test_no_data_is_returned_if_authentication_fails(status, target):
    # Arrange
    httpretty.register_uri(httpretty.POST, "https://tccna.honeywell.com/Auth/OAuth/Token",
                            body="token",
                            status = status,
                            content_type="application/json")
    # Act
    actual = target.read()

    # Assert
    assert not actual is True

@pytest.mark.unit
@pytest.mark.parametrize('status', [ 400, 429, 500, 503 ])
def test_no_data_is_returned_if_retrieving_location_info_fails(status, target):
    # Arrange
    httpretty.register_uri(httpretty.POST, "https://tccna.honeywell.com/Auth/OAuth/Token",
                            body=_account_info,
                            content_type="application/json")

    httpretty.register_uri(httpretty.GET,
                        "https://tccna.honeywell.com/WebAPI/emea/api/v1/location/installationInfo?userId=%s&includeTemperatureControlSystems=True" %
                        _account_info["userId"],
                        body="data",
                        status = status,
                        content_type="application/json")
    # Act
    actual = target.read()

    # Assert
    assert not actual is True

@pytest.mark.unit
@pytest.mark.parametrize('status', [ 400, 429, 500, 503 ])
def test_no_data_is_returned_if_retrieving_status_info_fails(status, target):
    # Arrange
    httpretty.register_uri(httpretty.POST, "https://tccna.honeywell.com/Auth/OAuth/Token",
                            body=_account_info,
                            content_type="application/json")
    httpretty.register_uri(httpretty.GET,
                        "https://tccna.honeywell.com/WebAPI/emea/api/v1/location/installationInfo?userId=%s&includeTemperatureControlSystems=True" %
                        _account_info["userId"],
                        body=_installation_info,
                        status = status,
                        content_type="application/json")
    httpretty.register_uri(httpretty.GET,
                        "https://tccna.honeywell.com/WebAPI/emea/api/v1/location/1/status?includeTemperatureControlSystems=True",
                        body="data",
                        status=status)
    # Act
    actual = target.read()

    # Assert
    assert not actual is True
