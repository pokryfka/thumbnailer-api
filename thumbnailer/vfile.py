"""
Provides unified file interface to local file, AWS S3 object and HTTP(s) resource.
"""
import os
import logging
from aws_xray_sdk.core import xray_recorder

logger = logging.getLogger(__name__)


# TODO: make common base excetion class with message property?


class InvalidURIException(ValueError):
    def __init__(self, uri, example=None):
        self._uri = uri
        self._example = example
        message = "Invalid path or URI: {0}".format(uri)
        if example is not None:
            message = message + ", example: " + example
        self._message = message
        super(InvalidURIException, self).__init__(message)

    @property
    def uri(self):
        return self._uri

    @property
    def message(self):
        return self._message


# TODO: implement for LocalFile and HttpFile, currently used only in S3
class NotFoundException(Exception):
    def __init__(self, uri):
        self._uri = uri
        message = "{0} does not exist".format(uri)
        self._message = message
        super(NotFoundException, self).__init__(message)

    @property
    def uri(self):
        return self._uri

    @property
    def message(self):
        return self._message


class ForbiddenException(Exception):
    def __init__(self, uri, action):
        self._uri = uri
        message = "Forbidden to {action} {uri}".format(action=action, uri=uri)
        self._message = message
        super(ForbiddenException, self).__init__(message)

    @property
    def uri(self):
        return self._uri

    @property
    def message(self):
        return self._message


# factory method
def vfile(path_or_uri):
    if S3File.isS3URI(path_or_uri):
        return S3File(path_or_uri)
    elif LocalFile.isFileURI(path_or_uri):
        return LocalFile(path_or_uri)
    else:
        raise InvalidURIException(path_or_uri)


# abstract class
class VFile:
    def __init__(self, uri):
        self._uri = uri

    @property
    def uri(self):
        return self._uri

    def exists(self):
        """Checks if the file exists.

        Returns True if the file exists, False otherwise.
        """
        raise NotImplementedError

    def read(self, size=-1):
        """Reads the content from the beginning.

        Provide the size in bytes, negative for the whole file.

        Raises exception in case of error.
        """
        raise NotImplementedError

    def write(self, data):
        raise NotImplementedError

    def remove(self):
        raise NotImplementedError

    def __str__(self):
        return self.uri


class LocalFile(VFile):
    def __init__(self, uri):
        if not LocalFile.isFileURI(uri):
            raise InvalidURIException(uri, "file://path or just path")

        if not uri.startswith("file://"):
            uri = "file://%s" % uri
        super(LocalFile, self).__init__(uri)

        self._path = uri[len("file://") :]

    @property
    def path(self):
        return self._path

    @staticmethod
    def isFileURI(uri):
        return (uri.startswith("file://") and uri.count("/") > 2) or "://" not in uri

    def exists(self):
        abs_path = os.path.abspath(self._path)
        return os.path.isfile(abs_path)

    def read(self, size=-1):
        abs_path = os.path.abspath(self._path)
        fh = open(abs_path, "rb")
        data = fh.read(size)
        # TODO: optimize open/close for now we just do one read or write operation for each instance
        fh.close()
        return data

    def write(self, data):
        abs_path = os.path.abspath(self._path)
        if isinstance(data, bytes):
            fh = open(abs_path, "wb")
        else:
            fh = open(abs_path, "w")
        size = fh.write(data)
        fh.close()
        if size == len(data):
            return True
        else:
            logger.error("Failed writing to %s" % self.uri)
            return False

    def remove(self):
        abs_path = os.path.abspath(self._path)
        try:
            os.remove(abs_path)
            return True
        except:
            logger.error("Failed removing %s" % self.uri)
            return False


class S3File(VFile):

    # TODO: this is supposed to be a singleton, is there a better way to do it in Python?
    _s3_client = None

    @staticmethod
    def isS3URI(uri):
        return uri.startswith("s3://") and uri.count("/") > 2

    @property
    def bucket_name(self):
        return self._bucket_name

    @bucket_name.setter
    def bucket_name(self, value):
        # TODO: test value?
        self._bucket_name = value

    @property
    def key(self):
        return self._key

    def __init__(self, uri):
        if not S3File.isS3URI(uri):
            raise InvalidURIException(uri, "s3://bucket/key")
        if not S3File._s3_client:
            import boto3

            S3File._s3_client = boto3.client("s3")
        VFile.__init__(self, uri)
        path = uri[len("s3://") :]
        i = path.index("/")
        self._bucket_name = path[:i]
        self._key = path[i + 1 :]

    def exists(self):
        # TODO: raise ForbiddenException
        try:
            _ = S3File._s3_client.get_object(Bucket=self.bucket_name, Key=self.key)
            return True
        except S3File._s3_client.exceptions.NoSuchKey:
            return False

    @xray_recorder.capture("S3File.read")
    def read(self, size=-1):
        try:
            obj = S3File._s3_client.get_object(Bucket=self.bucket_name, Key=self.key)
            fh = obj["Body"]
            if size > 0:
                data = fh.read(size)
            else:
                data = fh.read()
            return data
        except S3File._s3_client.exceptions.NoSuchKey as e:
            logger.error("Failed to read %s: %s" % (self.uri, e))
            raise NotFoundException(self.uri)
        except S3File._s3_client.exceptions.ClientError as e:
            logger.error("Not allowed to read %s: %s" % (self.uri, e))
            raise ForbiddenException(self.uri, "read")

    @xray_recorder.capture("S3File.write")
    def write(self, data):
        try:
            response = S3File._s3_client.put_object(
                Body=data, Bucket=self.bucket_name, Key=self.key
            )
            # TODO: throw if failed to write, make another exception type
            if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                return True
            else:
                logger.error("Failed writing to %s" % self.uri)
                return False
        except S3File._s3_client.exceptions.ClientError as e:
            # TODO: check type of ClientError
            logger.error("Not allowed to write %s: %s" % (self.uri, e))
            raise ForbiddenException(self.uri, "write")

    def remove(self):
        response = S3File._s3_client.delete_object(
            Bucket=self.bucket_name, Key=self.key
        )
        if response["ResponseMetadata"]["HTTPStatusCode"] == 204:
            return True
        else:
            logger.error("Failed removing %s" % self.uri)
            return False


# TODO: implement HTTPFile

# TODO: implement tests
