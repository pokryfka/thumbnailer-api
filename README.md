# thumbnail-api

REST interface to create thumbnails of images stored on AWS S3.

Thumbnails are optionally cached on (another) S3 bucket.

Used by [https://photos.pokryfka.net](https://photos.pokryfka.net)

## API

GET /thumbnail/{uri}/long-edge/{long_edge_pixels}

where:

- *{uri}* - URL encoded URI of the original image
- *{long_edge_pixels}* - size in pixels of the long edge

Supported URIs:

- *s3://bucket/key* - [AWS S3](https://aws.amazon.com/s3/) object, example *s3://pokryfka-test2/photoinfo/test1.jpg*

Example (using [HTTPie](https://httpie.org) HTTP client), note the *Accept* header:

```bash
http -v -d ${BASE_URL}/thumbnail/s3%3A%2F%2Fpokryfka-test%2Fphotoinfo%2Ftest1.jpg/long-edge/200 \
    Accept:image/jpg \
    X-API-Key:xxx
```

URI prefix can be optionally send as HTTP header:

```bash
http -v -d ${BASE_URL}/thumbnail/photoinfo%2Ftest1.jpg/long-edge/200 \
    Accept:image/jpg \
    URI-Prefix:s3://pokryfka-test/ \
    X-API-Key:xxx
```

## Configuration

### Caching

Set *CACHE_BUCKET* in ``.chalice/config.json`` to cache thumbnails on [AWS S3](https://aws.amazon.com/s3/).
Note that the policy in ``.chalice/policy-dev.json`` assumes that the thumbnails bucket name ends with *thumbnails*.
 
## Deploying

See bash ``./scripts/deploy.sh``` as well as [Chalice](https://github.com/aws/chalice/) for more information.

It is a good idea to make the [AWS API Gateway](https://aws.amazon.com/api-gateway/)
an origin of a [AWS CloudFront](https://aws.amazon.com/cloudfront/) distribution (or another CDN).

## Related Projects

- [Pillow](https://python-pillow.org) - The friendly PIL fork (Python Imaging Library)
- [Chalice](https://github.com/aws/chalice/) - Python Serverless Microframework for AWS

## TODO

- add scheduled functions checking and cleaning up the cache
- vfile tests
- support for HTTP uri?
- support for POSTing image data? see https://aws.amazon.com/blogs/developer/chalice-version-0-9-0-is-now-available/
