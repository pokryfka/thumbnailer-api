import boto3
import os
from uuid import uuid4
import logging
from .vfile import vfile


THUMBNAILS_BUCKET = GOOGLE_MAPS_API_KEY = os.environ.get('THUMBNAILS_BUCKET') or None


logger = logging.getLogger(__name__)


def _s3_bucket_key(uri):
    if not (uri.startswith('s3://') and uri.count('/') > 2):
        raise BaseException("Invalid URI format: %s, use s3://bucket_name/key" % uri)
    else:
        path = uri[len('s3://'):]
        i = path.index('/')
        bucket_name = path[:i]
        key = path[i + 1:]
        return bucket_name, key


def _cache_prefix(uri, long_edge_pixels):
    # does not contain the unique id and file extension
    bucket_name, key = _s3_bucket_key(uri)
    type = 's3' # later add support for different types
    path, filename_ext = os.path.split(key)
    filename, ext =  os.path.splitext(filename_ext)
    new_key = "%s_%s/long%spx/%s/%s" % (type, bucket_name, long_edge_pixels, path, filename)
    return "s3://%s/%s" % (THUMBNAILS_BUCKET, new_key)


def _create_cache_uri(uri, long_edge_pixels):
    """Returns *unique* URI to store cached file."""
    bucket_name, key = _s3_bucket_key(uri)
    type = 's3' # later add support for different types
    path, filename_ext = os.path.split(key)
    filename, ext =  os.path.splitext(filename_ext)
    unique = uuid4()
    new_key = "%s_%s/long%spx/%s/%s/%s%s" % (type, bucket_name, long_edge_pixels, path, filename, unique, ext)
    return "s3://%s/%s" % (THUMBNAILS_BUCKET, new_key)


def cache_data(data, uri, long_edge_pixels):
    """Stores data. Returns URI or None."""
    if THUMBNAILS_BUCKET is None:
        logger.error("THUMBNAILS_BUCKET is not defined")
        return None
    resized_uri = _create_cache_uri(uri, long_edge_pixels)
    f = vfile(resized_uri)
    f.write(data)
    return resized_uri


def list_cached_uris(uri, long_edge_pixels):
    """Returns array with URIs of cached objects. """
    if THUMBNAILS_BUCKET is None:
        logger.error("THUMBNAILS_BUCKET is not defined")
        return []
    # TODO: make the bucket singleton?
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(THUMBNAILS_BUCKET)
    prefix = _cache_prefix(uri, long_edge_pixels)[len("s3://%s" % THUMBNAILS_BUCKET)+1:]
    result = bucket.objects.filter(Prefix=prefix)
    return ["s3://%s/%s" % (o.bucket_name, o.key) for o in result]
