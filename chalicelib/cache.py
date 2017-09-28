import boto3
import os
from uuid import uuid4
import logging
from .vfile import S3File


logger = logging.getLogger(__name__)


class S3Cache:

    def __init__(self, bucket_name):
        """

        :param bucket_name:
        """

        if not isinstance(bucket_name, str):
            raise TypeError('bucket_name has to be str')
        if len(bucket_name) == 0:
            raise ValueError('bucket_name not set')
        self._bucket_name = bucket_name

    @property
    def bucket_name(self):
        return self._bucket_name


    def _check_src_uri(self, uri):
        s3uri = S3File(uri)

        if s3uri.bucket_name == self.bucket_name:
            raise ValueError("{uri} on CACHE_BUCKET".format(uri=uri))

    def _cache_prefix(self, uri, long_edge_pixels):
        # does not contain the unique id and file extension
        s3uri = S3File(uri)
        type = 's3'  # later add support for different types
        path, filename_ext = os.path.split(s3uri.key)
        filename, ext = os.path.splitext(filename_ext)
        new_key = "%s_%s/long%spx/%s/%s" % (type, s3uri.bucket_name, long_edge_pixels, path, filename)
        return "s3://%s/%s" % (self.bucket_name, new_key)

    def _create_cache_uri(self, uri, long_edge_pixels):
        """Returns *unique* URI to store cached file."""
        s3uri = S3File(uri)
        type = 's3'  # later add support for different types
        path, filename_ext = os.path.split(s3uri.key)
        filename, ext = os.path.splitext(filename_ext)
        unique = uuid4()
        new_key = "%s_%s/long%spx/%s/%s/%s%s" % (type, s3uri.bucket_name, long_edge_pixels, path, filename, unique, ext)
        return "s3://%s/%s" % (self.bucket_name, new_key)

    def write_data(self, data, src_uri, long_edge_pixels):
        """Stores data.

        Raises TypeError if data is not bytes.
        Raises ValueError if uri is not valid.
        Raises ValueError if uri is on the cache bucket.
        Raises TypeError if long_edge_pixels is not int.

        Returns URI of stored object or None."""

        if not isinstance(data, bytes):
            raise TypeError('data not bytes')
        self._check_src_uri(src_uri)

        resized_uri = self._create_cache_uri(src_uri, long_edge_pixels)
        f = S3File(resized_uri)
        f.write(data)
        return resized_uri

    def list_cached_uris(self, uri, long_edge_pixels):
        """Lists cached objects.

        Raises ValueError if uri is not valid.
        Raises ValueError if uri is on the cache bucket.
        Raises TypeError if long_edge_pixels is not int.

        Returns array with URIs of cached objects."""

        self._check_src_uri(uri)
        if not isinstance(long_edge_pixels, int):
            raise TypeError('long_edge_pixels is not int')

        # allow the cache directory to be a subdir
        i = self.bucket_name.find('/')
        if i > 0:
            bucket_name = self.bucket_name[:i]
        else:
            bucket_name = self.bucket_name

        # TODO: make the bucket singleton?
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(bucket_name)
        prefix = self._cache_prefix(uri, long_edge_pixels)[len("s3://%s" % bucket_name)+1:]
        result = bucket.objects.filter(Prefix=prefix)
        return ["s3://%s/%s" % (o.bucket_name, o.key) for o in result]
