"""Generate images of Tetris fields.

The goal of this module is to speed up output generation.
The current method of calling sfinder util fig can take several minutes if there are hundreds of solutions."""

import imageio, numpy, base64
from setupfinder import fumen


def get_blocks_from_skin(skin_filename):
    """Load block data from skin file (PNG format).
    
    There should be 9 blocks arranged horizontally. Blocks can be any size as long as height and width are equal.
    Should be arranged in fumen color order (blank, ILOZTJS, gray).
    """
    # use RGB mode to ignore alpha channel to cut down on filesize
    block_skin = imageio.imread(
        skin_filename, format="PNG", ignoregamma=True, pilmode="RGB")
    # count rows to get size, height and width should be the same
    height, width, _ = block_skin.shape
    # should be 9 for jstris/nullpo skin
    num_blocks = width // height
    blocks = numpy.hsplit(block_skin, num_blocks)
    return blocks


def fumen_to_image(fumen_data, height, blocks):
    """Convert fumen encoded field to base64 encoded PNG image (for embedding in output.html).

    height can be used to expand the field to a certain height with blank rows, should not be less than field height.
    blocks is a numpy array of block images in PNG format.
    """
    field, _ = fumen.decode(fumen_data)
    field_height = len(field)
    if (height > field_height):
        field.extend([[0] * 10 for _ in range(height - field_height)])
    # fumen.decode returns blocks in reverse order
    # could potentially speed things up even more by going straight from fumen to the proper format for this
    # and have a separate function to turn fumen output to a TetField
    field.reverse()
    img_data = numpy.vstack(
        tuple(numpy.hstack(tuple(blocks[i] for i in row)) for row in field))
    # for some reason optimize is giving me larger filesizes
    # imageio.imwrite("test.png", img_data, format="PNG", optimize=True
    png_data = imageio.imwrite(imageio.RETURN_BYTES, img_data, format="PNG")
    data_url = "data:image/png;base64," + base64.b64encode(png_data).decode()
    return data_url