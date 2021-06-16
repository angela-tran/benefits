"""
The enrollment application: Benefits Enrollment API implementation.
"""
import logging
from tempfile import NamedTemporaryFile
import time

import requests


logger = logging.getLogger(__name__)


class ApiError(Exception):
    """Error calling the enrollment APIs."""

    pass


class AccessTokenResponse:
    """Benefits Enrollment API Access Token response."""

    def __init__(self, response):
        logger.info("Read access token from response")

        try:
            payload = response.json()
        except ValueError:
            raise ApiError("Invalid response format")

        self.access_token = payload.get("access_token")
        self.token_type = payload.get("token_type")
        self.expires_in = payload.get("expires_in")
        if self.expires_in is not None:
            logger.debug("Access token has expiry")
            self.expiry = time.time() + self.expires_in
        else:
            logger.debug("Access token has no expiry")
            self.expiry = None

        logger.info("Access token successfully read from response")


class CustomerResponse:
    """Benefits Enrollment Customer API response."""

    def __init__(self, response, customer_id=None):
        logger.info("Read customer details from response")

        try:
            payload = response.json()
        except ValueError:
            raise ApiError("Invalid response format")

        self.id = payload.get("id", customer_id)
        self.customer_ref = payload.get("customer_ref")
        self.is_registered = str(payload.get("is_registered", "false")).lower() == "true"

        logger.info("Customer details successfully read from response")


class GroupResponse:
    """Benefits Enrollment Customer Group API response."""

    def __init__(self, response, requested_id, payload=None):
        if payload is None:
            try:
                payload = response.json()
            except ValueError:
                raise ApiError("Invalid response format")
        else:
            try:
                # Group API uses an error response (500) to indicate that the customer already exists in the group (!!!)
                # The error message should contain the customer ID we sent via payload
                error = response.json()["errors"][0]
                customer_id = payload[0]
                if not error["detail"].startswith("Duplicate") and customer_id in error["detail"]:
                    raise ApiError("Invalid response format")
            except (KeyError, ValueError):
                raise ApiError("Invalid response format")

        self.customer_ids = list(payload)
        self.updated_customer_id = self.customer_ids[0] if len(self.customer_ids) == 1 else None
        self.success = requested_id == self.updated_customer_id


class Client:
    """Benefits Enrollment API client."""

    def __init__(self, agency):
        logger.debug("Initialize Benefits Enrollment API Client")

        if agency is None:
            raise ValueError("agency")
        if agency.payment_processor is None:
            raise ValueError("agency.payment_processor")

        self.agency = agency
        self.provider = agency.payment_processor
        self.headers = {"Accept": "application/json", "Content-type": "application/json"}

    def _headers(self, headers=None):
        h = dict(self.headers)
        if headers:
            h.update(headers)
        return h

    def _make_url(self, *parts):
        return "/".join((self.provider.api_base_url, self.agency.merchant_id, *parts))

    def _get(self, url, payload, headers=None):
        h = self._headers(headers)
        return self._cert_request(lambda verify, cert: requests.get(url, headers=h, params=payload, verify=verify, cert=cert))

    def _patch(self, url, payload, headers=None):
        h = self._headers(headers)
        return self._cert_request(lambda verify, cert: requests.patch(url, headers=h, json=payload, verify=verify, cert=cert))

    def _post(self, url, payload, headers=None):
        h = self._headers(headers)
        return self._cert_request(lambda verify, cert: requests.post(url, headers=h, json=payload, verify=verify, cert=cert))

    def _cert_request(self, request_func):
        """
        Creates named (on-disk) temp files for client cert auth.
        * request_func: curried callable from `requests` library (e.g. `requests.get`).
        """
        # requests library reads temp files from file path
        # The "with" context destroys temp files when response comes back
        with NamedTemporaryFile("w+") as cert, NamedTemporaryFile("w+") as key, NamedTemporaryFile("w+") as ca:
            # write provider client cert data to temp files
            # resetting so they can be read again by requests
            cert.write(self.provider.client_cert_pem)
            cert.seek(0)

            key.write(self.provider.client_cert_private_key_pem)
            key.seek(0)

            ca.write(self.provider.client_cert_root_ca_pem)
            ca.seek(0)

            # request using temp file paths
            return request_func(verify=ca.name, cert=(cert.name, key.name))

    def _get_customer(self, token):
        """Get a customer record from Benefit Provider's system """
        logger.info("Check for existing customer record")

        if token is None:
            raise ValueError("token")

        url = self._make_url(self.provider.customers_endpoint)
        payload = {"token": token}

        try:
            r = self._get(url, payload)
            if r.status_code == 200:
                logger.debug("Customer record exists")
                customer = CustomerResponse(r)
                if customer.is_registered:
                    logger.debug("Customer is registered, skip update")
                    return customer
                else:
                    logger.debug("Customer is not registered, update")
                    return self._update_customer(customer.id, customer.customer_ref)
            else:
                r.raise_for_status()
        except requests.ConnectionError:
            raise ApiError("Connection to enrollment server failed")
        except requests.Timeout:
            raise ApiError("Connection to enrollment server timed out")
        except requests.TooManyRedirects:
            raise ApiError("Too many redirects to enrollment server")
        except requests.HTTPError as e:
            raise ApiError(e)

    def _update_customer(self, customer_id, customer_ref):
        """Update a customer using their unique info."""
        logger.info("Update existing customer record")

        if customer_id is None:
            raise ValueError("customer_id")
        if customer_ref is None:
            raise ValueError("customer_ref")

        url = self._make_url(self.provider.customer_endpoint, customer_id)
        payload = {"customer_ref": customer_ref, "is_registered": True}

        r = self._patch(url, payload)
        r.raise_for_status()

        return CustomerResponse(r)

    def access_token(self):
        """Obtain an access token to use for integrating with other APIs."""
        logger.info("Get new access token")

        url = self._make_url(self.provider.api_access_token_endpoint)
        payload = {self.provider.api_access_token_request_key: self.provider.api_access_token_request_val}

        try:
            r = self._post(url, payload)
            r.raise_for_status()
        except requests.ConnectionError:
            raise ApiError("Connection to enrollment server failed")
        except requests.Timeout:
            raise ApiError("Connection to enrollment server timed out")
        except requests.TooManyRedirects:
            raise ApiError("Too many redirects to enrollment server")
        except requests.HTTPError as e:
            raise ApiError(e)

        return AccessTokenResponse(r)

    def enroll(self, customer_token, group_id):
        """Enroll a customer in a product group using the token that represents that customer."""
        logger.info("Enroll customer in product group")

        if customer_token is None:
            raise ValueError("customer_token")
        if group_id is None:
            raise ValueError("group_id")

        customer = self._get_customer(customer_token)
        url = self._make_url(self.provider.group_endpoint, group_id)
        payload = [customer.id]

        try:
            r = self._patch(url, payload)

            if r.status_code in (200, 201):
                logger.info("Customer enrolled in group")
                return GroupResponse(r, customer.id)
            elif r.status_code == 500:
                logger.info("Customer already exists in group")
                return GroupResponse(r, customer.id, payload=payload)
            else:
                r.raise_for_status()
        except requests.ConnectionError:
            raise ApiError("Connection to enrollment server failed")
        except requests.Timeout:
            raise ApiError("Connection to enrollment server timed out")
        except requests.TooManyRedirects:
            raise ApiError("Too many redirects to enrollment server")
        except requests.HTTPError as e:
            raise ApiError(e)
