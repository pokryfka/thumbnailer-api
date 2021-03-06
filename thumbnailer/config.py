from os import getenv

try:
    with open("./version") as f:
        VER = f.read().rstrip()
except FileNotFoundError:
    version = "?"
RELEASE = "thumbnailer-{}".format(VER)
print("RELEASE: {}".format(RELEASE))
ENV = getenv("ENV", "DEV")
LOCAL_ENV = ENV.lower() == "LOCAL".lower()
print("ENV: {}".format(ENV))
print("LOCAL_ENV: {}".format(LOCAL_ENV))

LOG_LEVEL = getenv("LOG_LEVEL", "ERROR")

# see http://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Expiration.html#expiration-individual-objects
CONTENT_AGE_IN_SECONDS = int(getenv("CONTENT_AGE_IN_SECONDS", 10 * 60))

# X-Ray integration

from aws_xray_sdk.core import patch_all, xray_recorder

patch_all()


def put_annotation(key: str, value: str):
    segment = xray_recorder.current_subsegment()
    if segment:
        segment.put_annotation(key, value)


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


logging.basicConfig()
logging.getLogger().setLevel(LOG_LEVEL)


def handle_error(exception, message=None):
    if message:
        logging.warning(f"{message}: {exception}", exc_info=True)
    else:
        logging.warning(f"Error: {exception}", exc_info=True)
    capture_exception(exception)
