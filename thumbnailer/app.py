from json import dumps as json_dumps
from api_event_type import ApiEvent, ValidationError
from response_types import (
    JSONResultResponse,
    BinaryResultResponse,
    ServerErrorResponse,
    BadRequestResponse,
    NotFoundResponse,
    ForbiddenResponse,
)
from urllib.parse import unquote_plus
from config import handle_error, CONTENT_AGE_IN_SECONDS
from vfile import S3File, InvalidURIException, NotFoundException, ForbiddenException
from image_editor import get_size_image_data, resize_image_data, fit_image_data
import logging

INFO_RESOURCE_PREFIX = "/thumbnailer/info/"
THUMBNAIL_RESOURCE_PREFIX = "/thumbnailer/thumbnail/"
FIT_RESOURCE_PREFIX = "/thumbnailer/fit/"

CONTENT_HEADERS = {"Cache-Control": "max-age={0}".format(CONTENT_AGE_IN_SECONDS)}


def lambda_handler(event, context):
    logging.info("Received event: {}".format(json_dumps(event, indent=2)))

    try:
        event = ApiEvent(**event)
        logging.info("ApiEvent: {}".format(event.dict()))
        try:
            uri_encoded = event.pathParameters["uri"]
            # TODO: decode
            uri_encoded = "s3%3A%2F%2Fmyx-auth-dev-picturesbucket-2rm0spux6ue7%2Fprofile%2Ffb%2Ffb485679945593934.jpg"
            uri = unquote_plus(uri_encoded)
            if event.resource.startswith(INFO_RESOURCE_PREFIX):
                # TODO: pointer to function
                pass
            elif event.resource.startswith(THUMBNAIL_RESOURCE_PREFIX):
                long_edge_pixels = int(event.pathParameters["long_edge_pixels"])
            elif event.resource.startswith(FIT_RESOURCE_PREFIX):
                width_pixels = int(event.pathParameters["width_pixels"])
                height_pixels = int(event.pathParameters["height_pixels"])
            else:
                assert False
        except KeyError:
            raise ValueError

        if event.resource.startswith(INFO_RESOURCE_PREFIX):
            data = S3File(uri).read()
            image_size = get_size_image_data(data)
            info = dict(
                uri=uri,
                uri_encoded=uri_encoded,
                width=image_size[0],
                height=image_size[1],
            )
            return JSONResultResponse(body=info).dict()

        elif event.resource.startswith(THUMBNAIL_RESOURCE_PREFIX):
            data = S3File(uri).read()
            thumb_data = resize_image_data(data, long_edge_pixels)
            return BinaryResultResponse(
                data=thumb_data, content_type="image/jpg", headers=CONTENT_HEADERS
            ).dict()

        elif event.resource.startswith(FIT_RESOURCE_PREFIX):
            data = S3File(uri).read()
            thumb_data = fit_image_data(data, width_pixels, height_pixels)
            return BinaryResultResponse(
                data=thumb_data, content_type="image/jpg", headers=CONTENT_HEADERS
            ).dict()

        assert False
    except (ValidationError, InvalidURIException, ValueError) as e:
        handle_error(e)
        return BadRequestResponse().dict()
    except NotFoundException as e:
        handle_error(e)
        return NotFoundResponse().dict()
    except ForbiddenException as e:
        handle_error(e)
        return ForbiddenResponse().dict()
    except Exception as e:
        handle_error(e)
        return ServerErrorResponse().dict()
