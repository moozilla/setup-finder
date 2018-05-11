"""Methods for generating different types of setups and overlays and outputting fumen diagrams sfinder can use."""

import fumen

# reversed because TetField goes from bottom->top and I want it to be compatible
SHAPE_TSPIN = list(reversed([
    [0, 0, 2],
    [0, 0, 0],
    [2, 0, 2]])) # yapf: disable

SHAPE_TETRIS = [[0], [0], [0], [0]]


def prettify(field):
    reversed_field = field
    reversed_field.reverse()
    return "\n".join(
        ["".join(map(lambda b: "_X*." [b], row)) for row in reversed_field])


def generate_setup(field_height, cleared_rows, shape, shape_x, shape_y):
    """Generate field (in list form) to find setups for a shape at x,y that clears cleared_rows.
    
    Todo: this whole thing needs some error handling, especially the drop-in part
    """
    # initialize with all margin cells
    field = [[3] * 10 for _ in range(field_height)]

    # add fill requirement for rows to be cleared
    for y in cleared_rows:
        field[y] = [2] * 10

    # insert shape
    shape_width = len(shape[0])
    shape_height = len(shape)
    for y in range(shape_height):  # field goes from bottom->top
        for x in range(shape_width):
            field[shape_y + y][shape_x + x] = shape[y][x]

    return field


# note: all of these are "left-facing" in that the opening is on the left, the overhang on the right
#       if using for overlays (not 1st bag), you may need to mirror the generated setup to find right-facing spins
def generate_TSS1(field_height, x, y):
    field = generate_setup(field_height, [y - 1], SHAPE_TSPIN, x - 1, y - 1)
    # add opening for dropping in T piece
    for y in range(y + 2, field_height):
        field[y][x - 1] = 0
        field[y][x] = 0
    return field


def generate_TSS2(field_height, x, y):
    field = generate_setup(field_height, [y], SHAPE_TSPIN, x - 1, y - 1)
    for y in range(y + 2, field_height):
        field[y][x - 1] = 0
        field[y][x] = 0
    return field


def generate_TSD(field_height, x, y):
    field = generate_setup(field_height, [y - 1, y], SHAPE_TSPIN, x - 1, y - 1)
    for y in range(y + 2, field_height):
        field[y][x - 1] = 0
        field[y][x] = 0
    return field


def generate_Tetris(field_height, x, y):
    field = generate_setup(field_height, list(range(y, y + 4)), SHAPE_TETRIS,
                           x, y)
    # add opening for dropping in I piece (should there be an option to disable this?)
    for y in range(y + 4, field_height):
        field[y][x] = 0
    return field


def output_fumen(field, comment="-m o -f i -p [^T]!"):
    """Fix colors and add default sfinder args as comment."""
    # translate my field diagram into solid = gray, fill = I, margin = O
    fixed_colors = [[[0, 8, 1, 3][b] for b in row] for row in field]
    return fumen.encode([(fixed_colors, comment)])