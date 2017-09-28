from chalice import Chalice, Response, BadRequestError, NotFoundError, ForbiddenError
import urllib.parse
from hashlib import md5
from os import environ as env
import logging
import traceback
from chalicelib.image_editor import resize_image_data, MIN_LONG_EDGE, MAX_LONG_EDGE
from chalicelib.cache import S3Cache
from chalicelib.vfile import S3File, InvalidURIException, NotFoundException, ForbiddenException


DEBUG = env.get('DEBUG') == '1'

# see http://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Expiration.html#expiration-individual-objects
CONTENT_AGE_IN_SECONDS = 60*60


if DEBUG:
    logging.basicConfig(level=logging.INFO)
else:
    logging.basicConfig(level=logging.ERROR)

app = Chalice(app_name='thumbnailer-api')

app.log.setLevel(logging.INFO)

cache_bucket = env.get('CACHE_BUCKET') 
if cache_bucket is not None and len(cache_bucket) > 4:
    cache = S3Cache(cache_bucket)
else:
    cache = None


def _find_thumbnail_data(uri, long_edge_pixels):
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


def _image_data_response(data):
    checksum = md5()
    checksum.update(data)
    headers = { #'Content-Length': str(len(data)), # seems Chalice adds it anyway
                'Content-Type': 'image/jpg',
                'ETag': checksum.hexdigest(),
                'Cache-Control': "max-age=%d" % CONTENT_AGE_IN_SECONDS }
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
    if long_edge_pixels < MIN_LONG_EDGE or long_edge_pixels > MAX_LONG_EDGE:
        raise BadRequestError("long-edge must be >= {min_value} and <= {max_value}"
                              .format(min_value=MIN_LONG_EDGE, max_value=MAX_LONG_EDGE))
    app.log.info("Requested: %s @ %d" % (uri, long_edge_pixels))
    uri_prefix = request.headers.get('URI-Prefix')
    if uri_prefix is not None:
        app.log.info("URI-Prefix: {0}".format(uri_prefix))
        uri = uri_prefix + uri
    if cache is not None:
        app.log.info("CACHE_BUCKET = {0}".format(cache.bucket_name))
    try:
        image_data = None
        if cache is not None:
            image_data = _find_thumbnail_data(uri, long_edge_pixels)
        if image_data is None:
            image_data = _create_thumbnail_data(uri, long_edge_pixels)
            if cache is not None:
                _cache_thumbnail_data(image_data, uri, long_edge_pixels)
        return _image_data_response(image_data)
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


# TODO: test, run daily and check the cache?
#@app.schedule('rate(1 hour)')
#def every_hour(event):
#    print(event.to_dict())
