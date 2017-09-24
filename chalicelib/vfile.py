"""
Provides unified file interface to local file, AWS S3 object and HTTP(s) resource.
"""
import os
import logging

logger = logging.getLogger(__name__)


# TODO: implement for LocalFile and HttpFile, currently used only in S3
class NotFoundException(Exception):
    def __init__(self, uri):
        self._uri = uri
        message = "%s does not exist"
        super(NotFoundException, self).__init__(message)
    @property
    def uri(self):
        return self._uri


class ForbiddenException(Exception):
    def __init__(self, uri):
        self._uri = uri
        # TODO: specify read/list or write access
        message = "Access denied to %s" % uri
        super(ForbiddenException, self).__init__(message)
    @property
    def uri(self):
        return self._uri


# factory method
def vfile(path_or_uri):
    if S3File.isS3URI(path_or_uri):
        return S3File(path_or_uri)
    elif LocalFile.isFileURI(path_or_uri):
        return LocalFile(path_or_uri)
    else:
        # TODO: create Exception type?
        raise ValueError("Invalid path or URI" % path_or_uri)


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
            raise ValueError("Invalid File URI: %s, use file://path or just path" % uri)

        if not uri.startswith('file://'):
            uri = "file://%s" % uri
        super(LocalFile, self).__init__(uri)

        self._path = uri[len('file://'):]

    @property
    def path(self):
        return self._path

    @staticmethod
    def isFileURI(uri):
        return (uri.startswith('file://') and uri.count('/') > 2) or '://' not in uri

    def exists(self):
        abs_path = os.path.abspath(self._path)
        return os.path.isfile(abs_path)

    def read(self, size=-1):
        abs_path = os.path.abspath(self._path)
        fh = open(abs_path, 'rb')
        data = fh.read(size)
        # TODO: optimize open/close for now we just do one read or write operation for each instance
        fh.close()
        return data

    def write(self, data):
        abs_path = os.path.abspath(self._path)
        if isinstance(data, bytes):
            fh = open(abs_path, 'wb')
        else:
            fh = open(abs_path, 'w')
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

#import boto3
#from botocore.exceptions import ClientError
#from botocore.client import Config

#AWS_ACCESS_KEY=''
#AWS_SECRET_ACCESS_KEY=''

#AWS_CONFIG=dict(aws_access_key_id=AWS_ACCESS_KEY,
#                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
#                config=Config(signature_version='s3v4'))

#s3_client = boto3.client('s3', **AWS_CONFIG)
#s3_client = boto3.client('s3')


class S3File(VFile):
    # TODO: this is supposed to be a singleton, is there a better way to do it in Python?
    _s3_client = None
    @staticmethod
    def isS3URI(uri):
        return uri.startswith('s3://') and uri.count('/') > 2
    @property
    def bucket(self):
        return self._bucket
    @bucket.setter
    def bucket(self, value):
        # TODO: test value?
        self._bucket = value
    @property
    def key(self):
        return self._key
    def __init__(self, uri):
        if not S3File.isS3URI(uri):
            raise ValueError("Invalid S3URI: %s, use s3://bucket/key" % uri)
        if not S3File._s3_client:
            import boto3
            S3File._s3_client = boto3.client('s3')
        VFile.__init__(self, uri)
        path = uri[len('s3://'):]
        i = path.index('/')
        self._bucket = path[:i]
        self._key = path[i + 1:]
    def exists(self):
        # TODO: raise ForbiddenException
        try:
            _ = S3File._s3_client.get_object(Bucket=self.bucket, Key=self.key)
            return True
        except S3File._s3_client.exceptions.NoSuchKey:
            return False
    def read(self,size=-1):
        try:
            obj = S3File._s3_client.get_object(Bucket=self.bucket, Key=self.key)
            fh = obj['Body']
            if size > 0:
                data = fh.read(size)
            else:
                data = fh.read()
            return data
        except S3File._s3_client.exceptions.NoSuchKey as e:
            logger.error("Failed to read %s: %s" % (self.uri, e))
            raise NotFoundException(self.uri)
        except S3File._s3_client.exceptions.ClientError as e:
            # TODO: check type of ClientError
            logger.error("Not allowed to read %s: %s" % (self.uri, e))
            raise ForbiddenException(self.uri)
    def write(self,data):
        try:
            response = S3File._s3_client.put_object(Body=data, Bucket=self.bucket, Key=self.key)
            # TODO: throw if failed to write, make another exception type
            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                return True
            else:
                logger.error("Failed writing to %s" % self.uri)
                return False
        except S3File._s3_client.exceptions.ClientError as e:
            # TODO: check type of ClientError
            logger.error("Not allowed to write %s: %s" % (self.uri, e))
            raise ForbiddenException(self.uri)
    def remove(self):
        response = S3File._s3_client.delete_object(Bucket=self.bucket, Key=self.key)
        if response['ResponseMetadata']['HTTPStatusCode'] == 204:
            return True
        else:
            logger.error("Failed removing %s" % self.uri)
            return False

# TODO: implement HTTPFile

# TODO: implement tests
