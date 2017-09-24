# thumbnail-api

REST interface to create thumbnails of images stored on AWS S3.

Thumbnails are optionally cached on specified S3 bucket.

Used by [https://photos.pokryfka.net](https://photos.pokryfka.net)

## API

GET /thumbnail/{uri}/long-edge/{long_edge_pixels}

where

- *{uri}* - URL encoded URI of the original image
- *{long_edge_pixels}* - size in pixels of the long edge

Supported URIs:

- *s3://bucket/key* - [AWS S3](https://aws.amazon.com/s3/) object, example *s3://pokryfka-test2/photoinfo/test1.jpg*

Example (using [HTTPie](https://httpie.org) HTTP client), note the *Accept* header:

```bash
http -v -d 'localhost:8000/thumbnail/s3%3A%2F%2Fpokryfka-test%2Fphotoinfo%2Ftest1.jpg/long-edge/200' \
    Accept:image/jpg \
    X-API-Key:rpWPrqDne2aqBjB401lzOaLBNzMSVeYl91jHN457
```

## Caching

Set THUMBNAILS_BUCKET to cache thumbnails on [AWS S3](https://aws.amazon.com/s3/).
Update the bucket name ``.chalice/policy-dev.json``.

Example:

```bash
export THUMBNAILS_BUCKET=pokryfka-photos-thumbnails
```

It is recommended to add objects lifecycle rule to delete old images.

## Deploying

```bash
./scripts/deploy.sh
```

See [Chalice](https://github.com/aws/chalice/) for more information.


## Related Projects

- [Pillow](https://python-pillow.org) - The friendly PIL fork (Python Imaging Library)
- [Chalice](https://github.com/aws/chalice/) - Python Serverless Microframework for AWS

## TODO

- implemend http source in vfile?
- dont resize if the original image is smaller?
- tests
- POST image data? see https://aws.amazon.com/blogs/developer/chalice-version-0-9-0-is-now-available/
