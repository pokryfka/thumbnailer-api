from io import BytesIO
from PIL import Image
import logging


logger = logging.getLogger(__name__)


def resize_image_data(data, long_edge_pixels):
    """Resizes image data.

    Returns data with resized JPEG image.
    """
    b = BytesIO(data)
    im = Image.open(b)
    size = (long_edge_pixels, long_edge_pixels)
    im.thumbnail(size)
    output = BytesIO()
    im.save(output, 'JPEG')
    im.close()
    outdata = output.getvalue()
    logger.info("Resized %dx%d %d bytes to long%dpx %d bytes" % (im.size[0], im.size[1], len(data),
                                                                 long_edge_pixels, len(outdata)))
    return outdata
