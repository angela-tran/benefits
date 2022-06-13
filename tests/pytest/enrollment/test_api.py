import time

import requests

import pytest

from benefits.enrollment.api import ApiError, AccessTokenResponse, CustomerResponse, GroupResponse, Client


def test_AccessTokenResponse_invalid_response(mocker):
    mock_response = mocker.Mock()
    mock_response.json.side_effect = ValueError

    with pytest.raises(ApiError, match=r"response"):
        AccessTokenResponse(mock_response)


def test_AccessTokenResponse_valid_response(mocker):
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"access_token": "access123", "token_type": "mock"}

    response = AccessTokenResponse(mock_response)

    assert response.access_token == "access123"
    assert response.token_type == "mock"
    assert response.expiry is None


def test_AccessTokenResponse_valid_response_expires_in(mocker):
    expires_in = 100
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"expires_in": expires_in}

    start = time.time()
    response = AccessTokenResponse(mock_response)

    assert response.expiry >= start + expires_in


@pytest.mark.parametrize("exception", [KeyError, ValueError])
def test_CustomerResponse_invalid_response(mocker, exception):
    mock_response = mocker.Mock()
    mock_response.json.side_effect = exception

    with pytest.raises(ApiError, match=r"response"):
        CustomerResponse(mock_response)


def test_CustomerResponse_no_id(mocker):
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"id": None}

    with pytest.raises(ApiError, match=r"response"):
        CustomerResponse(mock_response)


def test_CustomerResponse(mocker):
    id = "12345"
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"id": id}

    response = CustomerResponse(mock_response)

    assert response.id == id
    assert not response.is_registered


@pytest.mark.parametrize("is_registered", ["true", "True", "tRuE"])
def test_CustomerResponse_is_registered(mocker, is_registered):
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"id": "12345", "is_registered": is_registered}

    response = CustomerResponse(mock_response)

    assert response.is_registered


@pytest.mark.parametrize("is_registered", ["false", "Frue", "fAlSe"])
def test_CustomerResponse_not_is_registered(mocker, is_registered):
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"id": "12345", "is_registered": is_registered}

    response = CustomerResponse(mock_response)

    assert not response.is_registered


def test_GroupResponse_no_payload_invalid_response(mocker):
    mock_response = mocker.Mock()
    mock_response.json.side_effect = ValueError

    with pytest.raises(ApiError, match=r"response"):
        GroupResponse(mock_response, 0)


def test_GroupResponse_no_payload_valid_response_single_matching_id(mocker):
    mock_response = mocker.Mock()
    mock_response.json.return_value = ["0"]

    response = GroupResponse(mock_response, "0")

    assert response.customer_ids == ["0"]
    assert response.updated_customer_id == "0"
    assert response.success
    assert response.message == ""


def test_GroupResponse_no_payload_valid_response_single_unmatching_id(mocker):
    mock_response = mocker.Mock()
    mock_response.json.return_value = ["1"]

    response = GroupResponse(mock_response, "0")

    assert response.customer_ids == ["1"]
    assert response.updated_customer_id == "1"
    assert not response.success
    assert "customer_id" in response.message


def test_GroupResponse_no_payload_valid_response_multiple_ids(mocker):
    mock_response = mocker.Mock()
    mock_response.json.return_value = ["0", "1"]

    response = GroupResponse(mock_response, "0")

    assert response.customer_ids == ["0", "1"]
    assert not response.updated_customer_id
    assert not response.success
    assert "customer_id" in response.message


@pytest.mark.parametrize("exception", [KeyError, ValueError])
def test_GroupResponse_payload_invalid_response(mocker, exception):
    mock_response = mocker.Mock()
    mock_response.json.side_effect = exception

    with pytest.raises(ApiError, match=r"response"):
        GroupResponse(mock_response, "0", [])


def test_GroupResponse_payload_valid_response(mocker):
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"errors": [{"detail": "Duplicate id 0"}]}

    response = GroupResponse(mock_response, "0", ["0"])

    assert response.customer_ids == ["0"]
    assert response.updated_customer_id == "0"
    assert response.success
    assert response.message == ""


failure_conditions = [
    # customer_id is None
    ({"detail": "Duplicate"}, [None]),
    # detail is None
    ({"detail": None}, ["0"]),
    # customer_id not in detail
    ({"detail": "1"}, ["0"]),
    # customer_id in detail, detail doesn't start with Duplicate
    ({"detail": "0"}, ["0"]),
]


@pytest.mark.parametrize("error,payload", failure_conditions)
def test_GroupResponse_payload_failure_response(mocker, error, payload):
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"errors": [error]}

    with pytest.raises(ApiError, match=r"response"):
        GroupResponse(mock_response, "0", payload)


def test_Client_init_no_agency():
    with pytest.raises(ValueError, match=r"agency"):
        Client(None)


def test_Client_init_no_payment_processor(mocker):
    mock_agency = mocker.Mock()
    mock_agency.payment_processor = None

    with pytest.raises(ValueError, match=r"payment_processor"):
        Client(mock_agency)


def test_Client_init(mocker):
    mock_agency = mocker.Mock()
    mock_agency.payment_processor = mocker.Mock()

    client = Client(mock_agency)

    assert client.agency == mock_agency
    assert client.payment_processor == mock_agency.payment_processor


@pytest.mark.django_db
@pytest.mark.parametrize(
    "exception", [requests.ConnectionError, requests.Timeout, requests.TooManyRedirects, requests.HTTPError]
)
def test_Client_access_token_exception(mocker, first_agency, exception):
    client = Client(first_agency)
    mock_response = mocker.Mock()
    mock_response.raise_for_status.side_effect = exception
    mocker.patch.object(client, "_post", return_value=mock_response)

    with pytest.raises(ApiError):
        client.access_token()


@pytest.mark.django_db
def test_Client_access_token(mocker, first_agency):
    client = Client(first_agency)
    mock_response = mocker.Mock()
    mocker.patch.object(client, "_post", return_value=mock_response)
    mocker.patch("benefits.enrollment.api.AccessTokenResponse")

    token = client.access_token()

    assert token


@pytest.mark.django_db
def test_Client_enroll_no_customer_token(first_agency):
    client = Client(first_agency)

    with pytest.raises(ValueError, match=r"customer_token"):
        client.enroll(None, "group_id")


@pytest.mark.django_db
def test_Client_enroll_no_group_id(first_agency):
    client = Client(first_agency)

    with pytest.raises(ValueError, match=r"group_id"):
        client.enroll("customer_token", None)
