import pytest
import os
from chalicelib.image_editor import resize_image_data, LONG_EDGE_MIN, LONG_EDGE_MAX
from chalicelib.vfile import vfile

# TODO: clean up paths
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


TESTDATA_PATH = os.path.join(os.path.dirname(__file__), 'testdata')


image_files = [
    'test1.jpg'
]

invalid_files = [
    'empty',
    'invalid.bin'
]

thumbnail_valid_sizes = [
    800,
    1200
]

thumbnail_invalid_sizes = [
    0,
    LONG_EDGE_MIN - 1,
    LONG_EDGE_MAX + 1
]


@pytest.fixture(params=image_files)
def image_data(request):
    path = os.path.join(TESTDATA_PATH, request.param)
    data = vfile(path).read()
    return data


@pytest.fixture(params=invalid_files)
def invalid_data(request):
    path = os.path.join(TESTDATA_PATH, request.param)
    data = vfile(path).read()
    return data


invalid_data_types = [
    str('DEADBEEF'),
    float(0),
    int(0)
]

@pytest.mark.parametrize("data", invalid_data_types)
def test_thumbnail_invalid_data_type(data):
    try:
        thumbnail_size = 1200
        _ = resize_image_data(data, thumbnail_size)
    except Exception as e:
        assert isinstance(e, TypeError)


invalid_long_edge_types = [
    float(800),
    str("800"),
]

@pytest.mark.parametrize("thumbnail_size", invalid_long_edge_types)
def test_thumbnail_invalid_size_type(invalid_data, thumbnail_size):
    try:
        _ = resize_image_data(invalid_data, thumbnail_size)
    except Exception as e:
        assert isinstance(e, TypeError)


@pytest.mark.parametrize("thumbnail_size", thumbnail_valid_sizes)
def test_thumbnail_invalid_data(invalid_data, thumbnail_size):
    try:
        _ = resize_image_data(invalid_data, thumbnail_size)
    except Exception as e:
        assert isinstance(e, IOError)


@pytest.mark.parametrize("thumbnail_size", thumbnail_invalid_sizes)
def test_thumbnail_invalid_size(invalid_data, thumbnail_size):
    try:
        _ = resize_image_data(invalid_data, thumbnail_size)
    except Exception as e:
        assert isinstance(e, ValueError)


@pytest.mark.parametrize("thumbnail_size", thumbnail_valid_sizes)
def test_thumbnail_positive(image_data, thumbnail_size):
    thumb_data = resize_image_data(image_data, thumbnail_size)
    assert isinstance(thumb_data, bytes)
    # TODO: verify that its a JPEG image and its resolution?
