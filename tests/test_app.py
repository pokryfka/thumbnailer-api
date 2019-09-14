import pytest
import subprocess
import requests
import urllib.parse


# TODO: make it nicer?
import os
CHALICE_WD = os.path.join(os.path.dirname(__file__), '..')

TIMEOUT_S = 30


valid_image_uris = [
    'photoinfo%2Ftest1.jpg'
]

_valid_image_bucket = 's3://pokryfka-test'
_valid_image_key = 'photoinfo/test1.jpg'
_valid_uri_prefix = _valid_image_bucket + '/'
_valid_image_uri = _valid_image_bucket + '/' + _valid_image_key
_forbidden_uri = 's3://idontknowwhat/key'
_valid_long_edge = 200

invalid_long_edges = [
    0,
    100,
    4000,
    400.5,
    'big'
]


# TODO: we shall test it with and without cache

@pytest.fixture(scope="session")
def base_url():
    # a bit nasty but does the trick
    # TODO: check if the port is available
    command = 'chalice local --port 8001'
    p = subprocess.Popen(command.split(' '), cwd=CHALICE_WD)
    yield 'http://localhost:8001'
    p.terminate()


def _thubnail_url(base_url, image_uri, long_edge):
    image_uri_encoded = urllib.parse.quote_plus(image_uri)
    url = "{base_url}/thumbnail/{uri}/long-edge/{size}"\
          .format(base_url=base_url, uri=image_uri_encoded, size=long_edge)
    print(url)
    return url

def _headers(uri_prefix=None):
    headers = {'Accept': 'image/jpg'}
    if uri_prefix is not None:
        #uri_prefix_encoded = urllib.parse.quote_plus(uri_prefix)
        headers['URI-Prefix'] = uri_prefix
    print(headers)
    return headers


def test_thumbnail_valid_uri_prefix(base_url):
    headers = _headers(_valid_uri_prefix)
    url = _thubnail_url(base_url, _valid_image_key, _valid_long_edge)
    r = requests.get(url, headers=headers, timeout=TIMEOUT_S)
    print("{0.status_code}\n{0.headers}\n\n{0.text}".format(r))
    assert r.status_code == 200


def test_thumbnail_valid_uri_noprefix(base_url):
    headers = _headers()
    url = _thubnail_url(base_url, _valid_image_uri, _valid_long_edge)
    r = requests.get(url, headers=headers, timeout=TIMEOUT_S)
    print("{0.status_code}\n{0.headers}\n\n{0.text}".format(r))
    assert r.status_code == 200


def test_thumbnail_invalid_uri_and_prefix(base_url):
    headers = _headers(_valid_uri_prefix)
    url = _thubnail_url(base_url, _valid_image_uri, _valid_long_edge)
    r = requests.get(url, headers=headers, timeout=TIMEOUT_S)
    print("{0.status_code}\n{0.headers}\n\n{0.text}".format(r))
    assert r.status_code == 404


def test_thumbnail_invalid_noheaders(base_url):
    headers = {}
    url = _thubnail_url(base_url, _valid_image_uri, _valid_long_edge)
    r = requests.get(url, headers=headers, timeout=TIMEOUT_S)
    print("{0.status_code}\n{0.headers}\n\n{0.text}".format(r))
    assert r.status_code == 400


def test_thumbnail_invalid_forbidden(base_url):
    headers = {}
    url = _thubnail_url(base_url, _forbidden_uri, _valid_long_edge)
    r = requests.get(url, headers=headers, timeout=TIMEOUT_S)
    print("{0.status_code}\n{0.headers}\n\n{0.text}".format(r))
    assert r.status_code == 403


# TODO: test URI to bucket with no access, URI which does not exist...


@pytest.mark.parametrize("long_edge", invalid_long_edges)
def test_thumbnail_invalid_size(base_url, long_edge):
    headers = _headers(_valid_uri_prefix)
    url = _thubnail_url(base_url, _valid_image_key, long_edge)
    r = requests.get(url, headers=headers, timeout=TIMEOUT_S)
    print("{0.status_code}\n{0.headers}\n\n{0.text}".format(r))
    assert r.status_code == 400
