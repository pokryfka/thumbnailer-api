from os import getenv

LOG_LEVEL = getenv("LOG_LEVEL", "ERROR")

# see http://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Expiration.html#expiration-individual-objects
CONTENT_AGE_IN_SECONDS = int(getenv("CONTENT_AGE_IN_SECONDS", 10 * 60))

from aws_xray_sdk.core import patch_all

patch_all()

import logging


logging.basicConfig()
logging.getLogger().setLevel(LOG_LEVEL)


import traceback


def handle_error(error, message=""):
    logging.error("{}: {}\n{}".format(message, error, traceback.format_exc()))
