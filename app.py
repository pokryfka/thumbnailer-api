from chalice import Chalice, Response, BadRequestError, NotFoundError, ForbiddenError
import urllib.parse
from hashlib import md5
import logging
import traceback
from chalicelib.image_editor import resize_image_data
from chalicelib.cache import list_cached_uris, cache_data
from chalicelib.vfile import vfile, NotFoundException, ForbiddenException


# see http://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Expiration.html#expiration-individual-objects
CONTENT_AGE_IN_SECONDS=60*60


app = Chalice(app_name='thumbnailer-api')

app.log.setLevel(logging.INFO)


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
def thumbnail_data(uri, long_edge_pixels):
    request = app.current_request
    app.log.debug("Request: %s" % request.to_dict())
    try:
        uri = urllib.parse.unquote_plus(uri)
        long_edge_pixels = int(long_edge_pixels)
        app.log.info("Requested: %s @ %d" % (uri, long_edge_pixels))
        uri_prefix = request.headers.get('URI-Prefix')
        if uri_prefix is not None:
            app.log.info("URI-Prefix: {0}".format(uri_prefix))
            uri = uri_prefix + uri
        # check cache first
        cached = list_cached_uris(uri, long_edge_pixels)
        if len(cached) > 0:
            app.log.debug("Found cached images: %s" % cached)
            image_uri = cached[0]
            app.log.info("Sending %s" % image_uri)
            image_data = vfile(image_uri).read()
            return _image_data_response(image_data)
        else:
            # otherwise resize it
            f = vfile(uri)
            data = f.read()
            resized_data = resize_image_data(data, long_edge_pixels)
            # and cache
            resized_uri = cache_data(resized_data, uri, long_edge_pixels)
            if resized_uri is not None:
                app.log.info("Wrote resized image to %s" % resized_uri)
            return _image_data_response(resized_data)
    except NotFoundException:
        raise NotFoundError
    except ForbiddenException:
        raise ForbiddenError
    except:
        error = traceback.format_exc()
        app.log.error("%s" % error)
        raise BadRequestError(error)
