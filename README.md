# thumbnail-api

REST interface to create thumbnails of images stored on AWS S3.

Thumbnails are optionally cached on (another) S3 bucket.

## API

```GET /thumbnail/{uri}/long-edge/{long_edge_pixels}```

where:

- *{uri}* - URL encoded URI of the original image
- *{long_edge_pixels}* - size in pixels of the long edge

returns a sized version of the image, aspect ratio is not changed;

```GET /thumbnail/{uri}/fit/width/{width}/height/{height}```

where:

- *{uri}* - URL encoded URI of the original image
- *{width}* - requested image width in pixels
- *{height}* - requested image height in pixels

returns a sized and cropped version of the image, cropped to the requested aspect ratio and size

Supported URIs:

- *s3://bucket/key* - [AWS S3](https://aws.amazon.com/s3/) object, example *s3://bucket_name/path/file.jpg*

The *{uri}* has to be URL encoded, example in Python:


```python
import urllib.parse

uri = 's3://bucket_name/path/file.jpg'
uri_encoded = urllib.parse.quote_plus(uri)
uri_decoded = urllib.parse.unquote_plus(uri_encoded)
```

Example query (using [HTTPie](https://httpie.org) HTTP client), note the *Accept* header:

```bash
http -v -d ${BASE_URL}/thumbnail/s3%3A%2F%2Fbucket_name%2Fpath%2Ffile.jpg/long-edge/200 \
    Accept:image/jpg \
    X-API-Key:xxx
```

URI prefix can be optionally send as HTTP header:

```bash
http -v -d ${BASE_URL}/thumbnail/path%2Ffile.jpg/long-edge/200 \
    Accept:image/jpg \
    URI-Prefix:s3://bucket_name/ \
    X-API-Key:xxx
```

## Setup

### Python

Setup Python environment using [virtualenv](https://virtualenv.pypa.io/en/stable/):

```bash
pip install virtualenv

virtualenv venv
source venv/bin/activate
```

Note: **make sure you are using  python3.6**.

Install required libraries:

```bash
pip install -r requirements.txt
```

### AWS

Set *AWS_PROFILE* to override the default profile when testing local.

## Configuration

Configuration is set using environmental variables.

Values set when deploying the package are set in ``.chalice/config.json``.

- *DEBUG* - set to 1 to change debug level
- *LONG_EDGE_MIN* - minimum value of requested image width or height in pixels, default value 100
- *LONG_EDGE_MAX* - maximum value of requested image width or height in pixels, default value 2000
- *CONTENT_AGE_IN_SECONDS* - sets TTL returned in *Cache-Control* header, see [expiration-individual-objects](http://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Expiration.html#expiration-individual-objects), default value 600 seconds
- *CACHE_BUCKET* - (optional) bucket to cache thumbnails

Note: the policy in ``.chalice/policy-dev.json`` assumes that the thumbnails bucket name ends with *thumbnails*.


## Deploying

See bash ``./scripts/deploy.sh`` as well as [Chalice](https://github.com/aws/chalice/) for more information.

It is a good idea to make the [AWS API Gateway](https://aws.amazon.com/api-gateway/)
an origin of a [AWS CloudFront](https://aws.amazon.com/cloudfront/) distribution (or another CDN).

## Related Projects

- [Pillow](https://python-pillow.org) - The friendly PIL fork (Python Imaging Library)
- [Chalice](https://github.com/aws/chalice/) - Python Serverless Microframework for AWS

