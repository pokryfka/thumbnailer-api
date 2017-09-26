from io import BytesIO
from PIL import Image
import logging


logger = logging.getLogger(__name__)


# see https://pillow.readthedocs.io/en/latest/handbook/concepts.html#filters-comparison-table
_RESAMPLE_FILTER=Image.LANCZOS
# see http://pillow.readthedocs.io/en/3.0.x/handbook/image-file-formats.html#jpeg
_JPEG_OPTS = dict(quality=75, optimize=True)


def resize_image_data(data, long_edge_pixels, dont_enlarge=True):
    """Resizes image data.

    Returns data with resized JPEG image.
    """
    b = BytesIO(data)
    im = Image.open(b)
    im_res = im.size
    if dont_enlarge and long_edge_pixels > max(im.width, im.height):
        logger.info("Image resolution {im_res[0]}x{im_res[1]} smaller than requested {0}px"
                    .format(long_edge_pixels, im_res=im_res))
        return data
    th_res = (long_edge_pixels, long_edge_pixels)
    im.thumbnail(th_res, resample=_RESAMPLE_FILTER)
    th_res = im.size
    output = BytesIO()
    im.save(output, 'JPEG', **_JPEG_OPTS)
    im.close()
    outdata = output.getvalue()
    logger.info("Resized {im_res[0]}x{im_res[1]} {im_size} bytes to {th_res[0]}x{th_res[1]} {th_size} bytes"
                .format(im_res=im_res, im_size=len(data), th_res=th_res, th_size=len(outdata)))
    return outdata
