from json import dumps as json_dumps
from response_types import ResultResponse, ServerErrorResponse

from config import handle_error
import logging


def lambda_handler(event, context):
    logging.debug("Received event: {}".format(json_dumps(event, indent=2)))

    try:
        # find the S3 object
        # TODO

        # resize
        # TODO

        # return the image
        # TODO

        return ResultResponse(body="OK").dict()
    except Exception as e:
        handle_error(e)
        return ServerErrorResponse().dict()
