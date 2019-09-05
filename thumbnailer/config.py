from os import getenv

LOG_LEVEL = getenv("LOG_LEVEL", "ERROR")

from aws_xray_sdk.core import patch_all

patch_all()

import logging


logging.basicConfig()
logging.getLogger().setLevel(LOG_LEVEL)


import traceback


def handle_error(error, message=""):
    logging.error("{}: {}\n{}".format(message, error, traceback.format_exc()))
