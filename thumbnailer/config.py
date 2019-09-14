from os import getenv

try:
    with open("./version") as f:
        VER = f.read()
except FileNotFoundError:
    version = "?"
RELEASE = "thumbnailer-{}".format(VER)
print("RELEASE: {}".format(RELEASE))
ENV = getenv("ENV", "DEV")
print("ENV: {}".format(ENV))

LOG_LEVEL = getenv("LOG_LEVEL", "ERROR")

# see http://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Expiration.html#expiration-individual-objects
CONTENT_AGE_IN_SECONDS = int(getenv("CONTENT_AGE_IN_SECONDS", 10 * 60))

# X-Ray integration

if ENV != "LOCAL":
    from aws_xray_sdk.core import patch_all

    patch_all()

# Sentry integration

SENTRY_DSN = getenv("SENTRY_DSN")

from sentry_sdk import capture_exception

if SENTRY_DSN and SENTRY_DSN.startswith("https://"):
    print("SENTRY_DSN: {}".format(SENTRY_DSN))
    import sentry_sdk
    from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        release=RELEASE,
        environment=ENV.lower(),
        integrations=[AwsLambdaIntegration()],
    )

# Logging

import logging
import traceback


logging.basicConfig()
logging.getLogger().setLevel(LOG_LEVEL)


def handle_error(exception, message=""):
    logging.error("{}: {}\n{}".format(message, exception, traceback.format_exc()))
    capture_exception(exception)
