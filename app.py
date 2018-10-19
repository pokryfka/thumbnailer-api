from chalice import Chalice, Response, BadRequestError, NotFoundError, ForbiddenError
import urllib.parse
from hashlib import md5
from os import getenv
import logging
import traceback
from chalicelib.image_editor import LONG_EDGE_MIN, LONG_EDGE_MAX, resize_image_data, fit_image_data
from chalicelib.cache import S3Cache
from chalicelib.vfile import S3File, InvalidURIException, NotFoundException, ForbiddenException


DEBUG = getenv('DEBUG') == '1'

if DEBUG:
    logging.basicConfig(level=logging.INFO)
else:
    logging.basicConfig(level=logging.ERROR)

app = Chalice(app_name='thumbnailer-api')

app.log.setLevel(logging.INFO)


# see http://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Expiration.html#expiration-individual-objects 
CONTENT_AGE_IN_SECONDS = int(getenv('CONTENT_AGE_IN_SECONDS', 10*60))

CACHE_BUCKET = getenv('CACHE_BUCKET')
if CACHE_BUCKET is not None and len(CACHE_BUCKET) > 4:
    cache = S3Cache(CACHE_BUCKET)
else:
    cache = None

# print the configuration
app.log.info("LONG_EDGE_MIN = {0}".format(LONG_EDGE_MIN))
app.log.info("LONG_EDGE_MAX = {0}".format(LONG_EDGE_MAX))
app.log.info("CONTENT_AGE_IN_SECONDS = {0}".format(CONTENT_AGE_IN_SECONDS))
app.log.info("CACHE_BUCKET = {0}".format(CACHE_BUCKET))


def _find_cached_thumbnail_data(uri, long_edge_pixels):
    # TODO: check if all Exceptions are handled
    cached = cache.list_cached_uris(uri, long_edge_pixels)
    if len(cached) > 0:
        app.log.debug("Found cached images: %s" % cached)
        image_uri = cached[0]
        app.log.info("Sending %s" % image_uri)
        image_data = S3File(image_uri).read()
        return image_data
    return None


def _cache_thumbnail_data(data, uri, long_edge_pixels):
    resized_uri = cache.write_data(data, uri, long_edge_pixels)
    if resized_uri is not None:
        app.log.info("Wrote resized image to %s" % resized_uri)


def _create_thumbnail_data(uri, long_edge_pixels):
    # TODO: check if all Exceptions are handled
    data = S3File(uri).read()
    thumb_data = resize_image_data(data, long_edge_pixels)
    return thumb_data


def _create_fit_data(uri, width, height):
    # TODO: check if all Exceptions are handled
    data = S3File(uri).read()
    thumb_data = fit_image_data(data, width, height)
    return thumb_data


def _image_data_response(data, cached=False):
    checksum = md5()
    checksum.update(data)
    headers = {
        #'Content-Length': str(len(data)), # seems Chalice adds it anyway
        'Content-Type': 'image/jpg',
        'ETag': checksum.hexdigest(),
        'Cache-Control': "max-age={0}".format(CONTENT_AGE_IN_SECONDS)
    }
    if cached:
        headers['X-Thumbnailer-API-Cache'] = 'Hit'
    else:
        headers['X-Thumbnailer-API-Cache'] = 'Missed'
    app.log.debug("Headers: %s" % headers)
    return Response(data,
                    status_code=200,
                    headers=headers)


@app.route('/thumbnail/{uri}/long-edge/{long_edge_pixels}',
           methods=['GET'],
           cors=True, api_key_required=True)
def thumbnail(uri, long_edge_pixels):
    request = app.current_request
    app.log.debug("Request: %s" % request.to_dict())
    uri = urllib.parse.unquote_plus(uri)
    try:
        long_edge_pixels = int(long_edge_pixels)
    except ValueError:
        raise BadRequestError("long-edge must be an integer")
    if long_edge_pixels < LONG_EDGE_MIN or long_edge_pixels > LONG_EDGE_MAX:
        raise BadRequestError("long-edge must be >= {min_value} and <= {max_value}"
                              .format(min_value=LONG_EDGE_MIN, max_value=LONG_EDGE_MAX))
    app.log.info("Requested: %s @ %d" % (uri, long_edge_pixels))
    uri_prefix = request.headers.get('URI-Prefix')
    if uri_prefix is not None:
        app.log.info("URI-Prefix: {0}".format(uri_prefix))
        uri = uri_prefix + uri
    if cache is not None:
        app.log.info("CACHE_BUCKET = {0}".format(cache.bucket_name))
    try:
        image_data = None
        cached = False
        if cache is not None:
            image_data = _find_thumbnail_data(uri, long_edge_pixels)
            cached = image_data is not None
        if image_data is None:
            image_data = _create_thumbnail_data(uri, long_edge_pixels)
            if cache is not None:
                _cache_thumbnail_data(image_data, uri, long_edge_pixels)
        if image_data is None: # should not happen
            raise NotFoundError
        return _image_data_response(image_data, cached)
    except InvalidURIException as e:
        raise BadRequestError(e.message)
    except NotFoundException as e:
        raise NotFoundError(e.message)
    except ForbiddenException as e:
        raise ForbiddenError(e.message)
    except:
        if DEBUG:
            error = traceback.format_exc()
            app.log.error("%s" % error)
            raise BadRequestError(error)
        else:
            raise ChaliceViewError


@app.route('/thumbnail/{uri}/fit/width/{width}/height/{height}',
           methods=['GET'],
           cors=True, api_key_required=True)
def thumbnail(uri, width, height):
    request = app.current_request
    app.log.debug("Request: %s" % request.to_dict())
    uri = urllib.parse.unquote_plus(uri)
    try:
        width = int(width)
    except ValueError:
        raise BadRequestError("width must be an integer")
    try:
        height = int(height)
    except ValueError:
        raise BadRequestError("height must be an integer")
    if width < LONG_EDGE_MIN or width > LONG_EDGE_MAX:
        raise BadRequestError("width must be >= {min_value} and <= {max_value}"
                              .format(min_value=LONG_EDGE_MIN, max_value=LONG_EDGE_MAX))
    if height < LONG_EDGE_MIN or width > LONG_EDGE_MAX:
        raise BadRequestError("height must be >= {min_value} and <= {max_value}"
                              .format(min_value=LONG_EDGE_MIN, max_value=LONG_EDGE_MAX))
    app.log.info("Requested: %s fit to (%d, %d)" % (uri, width, height))
    uri_prefix = request.headers.get('URI-Prefix')
    if uri_prefix is not None:
        app.log.info("URI-Prefix: {0}".format(uri_prefix))
        uri = uri_prefix + uri
    if cache is not None:
        app.log.info("CACHE_BUCKET = {0}".format(cache.bucket_name))
    try:
        image_data = None
        # TODO: implement local caching for fit images
        cached = False
        #if cache is not None:
        #    image_data = _find_fit_data(uri, width, height)
        #    cached = image_data is not None
        if image_data is None:
            image_data = _create_fit_data(uri, width, height)
        #    if cache is not None:
        #        _cache_fit_data(image_data, uri, width, height)
        if image_data is None: # should not happen
            raise NotFoundError
        return _image_data_response(image_data, cached)
    except InvalidURIException as e:
        raise BadRequestError(e.message)
    except NotFoundException as e:
        raise NotFoundError(e.message)
    except ForbiddenException as e:
        raise ForbiddenError(e.message)
    except:
        if DEBUG:
            error = traceback.format_exc()
            app.log.error("%s" % error)
            raise BadRequestError(error)
        else:
            raise ChaliceViewError
