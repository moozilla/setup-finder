"""Methods for generating different types of setups and overlays and outputting fumen diagrams sfinder can use."""

# reversed because TetField goes from bottom->top and I want it to be compatible
SHAPE_TSPIN = list(reversed([
    [0, 0, 2],
    [0, 0, 0],
    [2, 0, 2]])) # yapf: disable

def prettify(field):
    reversed_field = field
    reversed_field.reverse()
    return "\n".join(
        ["".join(map(lambda b: "_X*." [b], row)) for row in reversed_field])


def generateSetup(field_height, cleared_rows, shape, shape_x, shape_y):
    """Generate field (in list form) to find setups for a shape at x,y that clears cleared_rows.
    
    Todo: this whole thing needs some error handling, especially the drop-in part
    """
    # initialize with all margin cells
    field = [[3] * 10 for _ in range(field_height)]

    # add fill requirement for rows to be cleared
    for y in cleared_rows:
        field[y] = [2] * 10

    # insert shape
    for y in range(3):  # field goes from bottom->top
        for x in range(3):
            field[shape_y + y][shape_x + x] = shape[y][x]

    # make opening for dropping T in - todo: this will need to be different for shapes w/ overhang (eg. TST)
    for y in range(shape_y + 3, field_height):
        field[y][shape_x] = 0
        field[y][shape_x + 1] = 0

    return field


# note: all of these are "left-facing" in that the opening is on the left, the overhang on the right
#       if using for overlays (not 1st bag), you may need to mirror the generated setup to find right-facing spins
def generateTSS1(field_height, x, y):
    return generateSetup(field_height, [y - 1], SHAPE_TSPIN, x - 1, y - 1)


def generateTSS2(field_height, x, y):
    return generateSetup(field_height, [y], SHAPE_TSPIN, x - 1, y - 1)


def generateTSD(field_height, x, y):
    return generateSetup(field_height, [y - 1, y], SHAPE_TSPIN, x - 1, y - 1)


def main():
    # generate a TSS1 (bottom row clear) centered on 1,1
    field = generateTSD(6, 1, 1)
    print(prettify(field))


if __name__ == '__main__':
    main()