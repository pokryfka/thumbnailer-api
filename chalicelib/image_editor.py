from os import getenv
from io import BytesIO
from PIL import Image, ExifTags
from PIL.ImageOps import fit as image_fit
import logging


logger = logging.getLogger(__name__)


LONG_EDGE_MIN = int(getenv('LONG_EDGE_MIN', 100))
LONG_EDGE_MAX = int(getenv('LONG_EDGE_MAX', 2000))

# see https://pillow.readthedocs.io/en/latest/handbook/concepts.html#filters-comparison-table
#RESAMPLE_FILTER=Image.LANCZOS
RESAMPLE_FILTER=Image.BICUBIC

# see https://pillow.readthedocs.io/en/latest/handbook/image-file-formats.html#jpeg
JPEG_OPTS = dict(quality=75, optimize=True)


def resize_image_data(data, long_edge_pixels, dont_enlarge=True):
    """Resizes image data.

    Raises TypeError if data is not bytes.
    Raises TypeError if long_edge_pixels is not int.
    Raises ValueError if long_edge_pixels is < LONG_EDGE_MIN or > LONG_EDGE_MAX.
    Raises IOError if the data is not a valid JPEG image.

    Returns data (bytes) with resized JPEG image.
    """

    if not isinstance(long_edge_pixels, int):
        raise TypeError('long_edge_pixels is not int')
    if long_edge_pixels < LONG_EDGE_MIN or long_edge_pixels > LONG_EDGE_MAX:
        raise ValueError("MIN_LONG_EDGE = {0}, MAX_LONG_EDGE = {1}".format(LONG_EDGE_MIN, LONG_EDGE_MAX))

    b = BytesIO(data)
    im = Image.open(b)
    im_res = im.size
    if dont_enlarge and long_edge_pixels > max(im.width, im.height):
        logger.info("Image resolution {im_res[0]}x{im_res[1]} smaller than requested {0}px"
                    .format(long_edge_pixels, im_res=im_res))
        return data
    th_res = (long_edge_pixels, long_edge_pixels)
    im = _process_exif_data(im)
    im.thumbnail(th_res, resample=RESAMPLE_FILTER)
    if im.mode != 'RGB':
        im = im.convert('RGB')
    th_res = im.size
    output = BytesIO()
    im.save(output, 'JPEG', **JPEG_OPTS)
    im.close()
    outdata = output.getvalue()
    logger.info("Resized {im_res[0]}x{im_res[1]} {im_size} bytes to {th_res[0]}x{th_res[1]} {th_size} bytes"
                .format(im_res=im_res, im_size=len(data), th_res=th_res, th_size=len(outdata)))
    return outdata


def fit_image_data(data, width, height):
    """Fits image data that is
    returns a sized and cropped version of the image, cropped to the requested aspect ratio and size.

    Raises TypeError if data is not bytes.
    Raises TypeError if width or height is not int.
    Raises ValueError if width or height is < LONG_EDGE_MIN or > LONG_EDGE_MAX.
    Raises IOError if the data is not a valid JPEG image.

    Returns data (bytes) with resized and cropped JPEG image.
    """

    if not isinstance(width, int):
        raise TypeError('width is not int')
    if not isinstance(height, int):
        raise TypeError('height is not int')
    if width < LONG_EDGE_MIN or width > LONG_EDGE_MAX:
        raise ValueError("MIN_LONG_EDGE = {0}, MAX_LONG_EDGE = {1}".format(LONG_EDGE_MIN, LONG_EDGE_MAX))
    if height < LONG_EDGE_MIN or height > LONG_EDGE_MAX:
        raise ValueError("MIN_LONG_EDGE = {0}, MAX_LONG_EDGE = {1}".format(LONG_EDGE_MIN, LONG_EDGE_MAX))

    b = BytesIO(data)
    im = Image.open(b)
    im_res = im.size
    th_res = (width, height)
    im = _process_exif_data(im)
    im = image_fit(im, th_res, method=RESAMPLE_FILTER)
    if im.mode != 'RGB':
        im = im.convert('RGB')
    th_res = im.size
    output = BytesIO()
    im.save(output, 'JPEG', **JPEG_OPTS)
    im.close()
    outdata = output.getvalue()
    logger.info("Fit {im_res[0]}x{im_res[1]} {im_size} bytes to {th_res[0]}x{th_res[1]} {th_size} bytes"
                .format(im_res=im_res, im_size=len(data), th_res=th_res, th_size=len(outdata)))
    return outdata


def _process_exif_data(img):
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = dict(img._getexif().items())

        if exif[orientation] == 3:
            img = img.rotate(180, expand=True)
        elif exif[orientation] == 6:
            img = img.rotate(270, expand=True)
        elif exif[orientation] == 8:
            img = img.rotate(90, expand=True)
    except Exception:
        pass
    return img
