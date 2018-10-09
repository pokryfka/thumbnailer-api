# thumbnail-api

REST interface to create thumbnails of images stored on AWS S3.

Thumbnails are optionally cached on (another) S3 bucket.

## API

GET /thumbnail/{uri}/long-edge/{long_edge_pixels}

where:

- *{uri}* - URL encoded URI of the original image
- *{long_edge_pixels}* - size in pixels of the long edge

Supported URIs:

- *s3://bucket/key* - [AWS S3](https://aws.amazon.com/s3/) object, example *s3://pokryfka-test2/photoinfo/test1.jpg*

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
pip install -r requirements.txt
```

### AWS

Set *AWS_PROFILE* to override the default profile when testing local.

## Configuration

### Caching

Set *CACHE_BUCKET* in ``.chalice/config.json`` to cache thumbnails on [AWS S3](https://aws.amazon.com/s3/).
Note that the policy in ``.chalice/policy-dev.json`` assumes that the thumbnails bucket name ends with *thumbnails*.
 
## Deploying

See bash ``./scripts/deploy.sh`` as well as [Chalice](https://github.com/aws/chalice/) for more information.

It is a good idea to make the [AWS API Gateway](https://aws.amazon.com/api-gateway/)
an origin of a [AWS CloudFront](https://aws.amazon.com/cloudfront/) distribution (or another CDN).

## Related Projects

- [Pillow](https://python-pillow.org) - The friendly PIL fork (Python Imaging Library)
- [Chalice](https://github.com/aws/chalice/) - Python Serverless Microframework for AWS

