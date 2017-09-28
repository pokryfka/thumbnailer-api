import pytest
import os
import uuid
from chalicelib.cache import S3Cache

# TODO: clean up paths
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


CACHE_BUCKET = "pokryfka-test/tmp/thumbnailer-api_test_cache_{0}".format(uuid.uuid1())


invalid_data_types = [
    str('DEADBEEF'),
    float(0),
    int(0)
]

valid_uris = [
    's3://pokryfka-test/photoinfo/test.jpg'
]

invalid_uris = [
    '',
    'invalid',
    'invalid/invalid',
    's3:invalid',
    's3:/invalid',
    ' s3://invalid',
    'http://invalid',
    "s3://{bucket_name}/key".format(bucket_name=CACHE_BUCKET)
]

invalid_long_edge_types = [
    float(800),
    str("800"),
]

_valid_uri = valid_uris[0]
_valid_uri_dont_exist = "s3://pokryfka-test/{0}".format(uuid.uuid1())
_valid_data = b'TEST'
_valid_long_edge = 1200
_invalid_long_edge = invalid_long_edge_types[0]


@pytest.fixture()
def cache():
    yield S3Cache(CACHE_BUCKET)
    # TODO: clean


@pytest.mark.parametrize("data", invalid_data_types)
def test_cache_write_invalid_data_type(cache, data):
    try:
        uri = _valid_uri
        long_edge = _valid_long_edge
        _ = cache.write_data(data, uri, long_edge)
    except Exception as e:
        assert isinstance(e, TypeError)


@pytest.mark.parametrize("uri", invalid_uris)
def test_cache_write_invalid_uri(cache, uri):
    try:
        data = _valid_data
        long_edge = _invalid_long_edge
        _ = cache.write_data(data, uri, long_edge)
    except Exception as e:
        if uri.startswith("s3://{bucket_name}/".format(bucket_name=cache.bucket_name)):
            assert isinstance(e, ValueError)
        else:
            assert isinstance(e, ValueError)


@pytest.mark.parametrize("long_edge", invalid_long_edge_types)
def test_cache_write_invalid_size_type(cache, long_edge):
    try:
        data = _valid_data
        uri = _valid_uri
        _ = cache.write_data(data, uri, long_edge)
    except Exception as e:
        assert isinstance(e, TypeError)


def test_cache_write_positive(cache):
    data = _valid_data
    uri = _valid_uri
    long_edge = _valid_long_edge
    new_uri = cache.write_data(data, uri, long_edge)
    assert new_uri is not None


# testing of actual writing shall be part of vfile tests


@pytest.mark.parametrize("uri", invalid_uris)
def test_cache_list_invalid_uri(cache, uri):
    long_edge = _valid_long_edge
    try:
        _ = cache.list_cached_uris(uri, long_edge)
    except Exception as e:
        if uri.startswith("s3://{bucket_name}/".format(bucket_name=cache.bucket_name)):
            assert isinstance(e, ValueError)
        else:
            assert isinstance(e, ValueError)


@pytest.mark.parametrize("long_edge", invalid_long_edge_types)
def test_cache_list_invalid_size_type(cache, long_edge):
    uri = _valid_uri
    try:
        _ = cache.list_cached_uris(uri, long_edge)
    except Exception as e:
        assert isinstance(e, TypeError)


def test_cache_list_noresults(cache):
    valid_uri = _valid_uri_dont_exist
    long_edge = _valid_long_edge
    result = cache.list_cached_uris(valid_uri, long_edge)
    assert len(result) == 0


def test_cache_list_positive(cache):
    count = 4
    data = _valid_data
    uri = _valid_uri
    long_edge = _valid_long_edge
    for i in range(count):
        _ = cache.write_data(data, uri, long_edge)
        result = cache.list_cached_uris(uri, long_edge)
        assert len(result) > i
