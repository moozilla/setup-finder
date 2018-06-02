"""Perform deeper analysis of setups.

This module is intended to be used in conjunction with the finder module. It will contain methods that:
* Determine what bags can be used to build a setup
* Find the specific keypresses/finesses used to perform a setup
* Score a setup based on completion percent or keypresses used
  (or est. time to complete taking into account various delays)
* From a list of setups, find a minimal system that covers 100% of bags and score overall system
"""

from copy import deepcopy
from setupfinder.finder import fumen

PIECE_I = [[[0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]], [[0, 0, 1, 0], [0, 0, 1, 0], [0, 0, 1, 0],
                                                                      [0, 0, 1, 0]],
           [[0, 0, 0, 0], [0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0]], [[0, 1, 0, 0], [0, 1, 0, 0], [0, 1, 0, 0],
                                                                      [0, 1, 0, 0]]]

PIECE_L = [[[2, 0, 0], [2, 2, 2], [0, 0, 0]], [[0, 2, 2], [0, 2, 0], [0, 2, 0]], [[0, 0, 0], [2, 2, 2], [0, 0, 2]],
           [[0, 2, 0], [0, 2, 0], [2, 2, 0]]]

PIECE_O = [[[3, 3], [3, 3]], [[3, 3], [3, 3]], [[3, 3], [3, 3]], [[3, 3], [3, 3]]]

PIECE_Z = [[[0, 4, 4], [4, 4, 0], [0, 0, 0]], [[0, 4, 0], [0, 4, 4], [0, 0, 4]], [[0, 0, 0], [0, 4, 4], [4, 4, 0]],
           [[4, 0, 0], [4, 4, 0], [0, 4, 0]]]

PIECE_T = [[[0, 5, 0], [5, 5, 5], [0, 0, 0]], [[0, 5, 0], [0, 5, 5], [0, 5, 0]], [[0, 0, 0], [5, 5, 5], [0, 5, 0]],
           [[0, 5, 0], [5, 5, 0], [0, 5, 0]]]

PIECE_J = [[[0, 0, 6], [6, 6, 6], [0, 0, 0]], [[0, 6, 0], [0, 6, 0], [0, 6, 6]], [[0, 0, 0], [6, 6, 6], [6, 0, 0]],
           [[6, 6, 0], [0, 6, 0], [0, 6, 0]]]

PIECE_S = [[[7, 7, 0], [0, 7, 7], [0, 0, 0]], [[0, 0, 7], [0, 7, 7], [0, 7, 0]], [[0, 0, 0], [7, 7, 0], [0, 7, 7]],
           [[0, 7, 0], [7, 7, 0], [7, 0, 0]]]

PIECES = {'I': PIECE_I, 'L': PIECE_L, 'O': PIECE_O, 'Z': PIECE_Z, 'T': PIECE_T, 'J': PIECE_J, 'S': PIECE_S}


# calculate valid placements for each piece/rotation
# next with generator to find first column with filled block, if no filled block defaults to 5 (bigger than any piece)
def _min_x(piece):
    return 0 - min([next((i for i, x in enumerate(row) if x), 5) for row in piece])


def _max_x(piece):
    return (10 - len(piece[0])) + min([next((i for i, x in enumerate(reversed(row)) if x), 5) for row in piece])


# none should make it throw an exception if piece is empty
def _min_y(piece):
    return 0 - next((i for i, row in enumerate(piece) if any(row)), None)


def _max_y(piece):
    """ unlike max_x this is relative to the bottom of the bounding box, not the bottom of the actual piece
    it represents the maximum-y value of the piece that contains a block
    """
    return len(piece) - next((i for i, row in enumerate(reversed(piece)) if any(row)), None)


def _occupied_cols(piece):
    """ Returns a list of which cols are occupied in a piece.

    Ex: >>> list(map(_occupied_cols, PIECE_I))
        [[0, 1, 2, 3], [2], [0, 1, 2, 3], [1]]
    """
    return [i for i, row in enumerate(zip(*piece)) if any(row)]


# maybe this should be in some sort of object? I'll wait to see how I use it.
VALID_X_PLACEMENTS = {key: [range(_min_x(rot), _max_x(rot) + 1) for rot in piece] for key, piece in PIECES.items()}
MIN_Y_PLACEMENT = {key: [_min_y(rot) for rot in piece] for key, piece in PIECES.items()}
MAX_Y_OFFSET = {key: [_max_y(rot) for rot in piece] for key, piece in PIECES.items()}
OCCUPIED_COLS = {key: [_occupied_cols(rot) for rot in piece] for key, piece in PIECES.items()}


def find_placements(field):
    """Determine how each piece is placed in a given field.

    This uses function uses the colors of each piece to locate it. Gray blocks are not considered.
    Some assumptions made for now:
    * At most 1 of each piece (one full bag or less)
    * Pieces aren't split by line clears (eg. as in output of sfinder path)
    Since this is intended to be used on output from sfinder setup for a single bag, these
    restrictions should make the method more simple and not be limiting. (For sfinder path,
    we could potentially use the --split flag or CSV output to get the piece order.)

    Args:
        field:  Tetris field in multidimensional list form. Should follow fumen colors, but rows
                should be in bottom up order.

    Returns:
        dict with pieces as key, (x,y,rotation) tuple as values, ex:
            {"T": (1,1,2), "O": (3,0,0)}
        Coordinates are based on bottom-left corner of piece's bounding box.
        Rotations are 0-3, with 2 being spawn orientation and increasing values by CCW rotates.
        (This is to match how fumen does it.)
    """

    #colors = " ILOZTJSG"

    return {piece: find_placement(piece, field) for piece in "ILOZTJS"}


def find_placement(piece, field):
    """Find a particular piece in a field.

    Expects exactly one piece to be present in field.
    (Maybe should do zero or one, and return None for no piece.)

    Args:
        piece: A piece in "ILOZTJS"
        field: Tetris field in multidimensional list form. See find_piece_locations for details.

    Returns:
        (x, y, rotation) tuple. See find_piece_locations for details.

    Raises exceptions if piece not found or invalid. (Return None instead?)
    """
    color = " ILOZTJSG".index(piece)
    piece_data = PIECES[piece]
    piece_size = len(piece_data[0])
    blocks = [(x, y) for y in range(len(field)) for x in range(10) if field[y][x] == color]
    if not blocks:
        return None
    if len(blocks) != 4:
        raise ValueError(f"Wrong amount of {piece}-color blocks, should be 4, found {len(blocks)}.")
    boxes = (get_bounding_boxes(blocks, piece_size))
    for x, y in boxes:
        # check starting with 2 because 2 is spawn position
        for rot in [2, 3, 0, 1]:
            if piece_is_at(field, piece_data[rot], x, y):
                return (x, y, rot)
    return None


def piece_is_at(field, piece, x, y):
    """Check if piece is at a particular (x,y) in field.

    Piece is a particular rotation state of a piece (should be a square list).
    """
    field_height = len(field)
    piece_size = len(piece[0])
    for py in range(piece_size):
        for px in range(piece_size):
            val = piece[py][px]
            if val > 0:
                # make sure piece is inbounds before checking if in correct spot
                if y + py < 0 or y + py > field_height - 1:
                    return False
                if x + px < 0 or x + px > 9:
                    return False
                if field[y + py][x + px] != val:
                    return False
    return True


def get_bounding_boxes(blocks, size):
    """Get possible bounding boxes for pieces.

    Used to find potential locations pieces could be in based on blocks.
    Args:
        blocks - list of (x,y) coords of each block in the piece
        size - should be 2 for O, 4 for I, 3 for other pieces
    """
    xs, ys = zip(*blocks)  # get x and y coords in separate lists
    x_span = max(xs) - min(xs)
    y_span = max(ys) - min(ys)
    if x_span > (size - 1) or y_span > (size - 1):
        raise ValueError("Blocks too spread out to fit in bounding box.")
    # Distance from min the bottom/left coord could be
    x_spread = size - x_span - 1
    y_spread = size - y_span - 1
    return [(x, y) for y in range(min(ys) - y_spread,
                                  max(ys) - y_span + 1) for x in range(min(xs) - x_spread,
                                                                       max(xs) - x_span + 1)]


def is_bag_possible(field, bag):
    """Determine if it's possible to perform setup with a particular bag.

    For now this tests only if pieces can be harddropped in, with no hold.

    Args:
        field - in list form like other functions in this module
        bag - string of pieces in order, eg. "TSOLIZJ"
    Returns True or False
    """
    placements = find_placements(field)
    #new_field = [[0] * 10 for _ in range(len(field))]
    new_field = [[0] * 10 for _ in range(20)]
    for piece in bag:
        if not is_harddrop_possible(piece, placements[piece], new_field):
            return False
        # place piece into new_field
        place_piece(piece, placements[piece], new_field)
    return True


def place_piece(piece, placement, field):
    """Update field by placing a piece.

    Expects placement to be validated beforehand.
    
    Args:
        piece - A piece in "ILOZTJS"
        placement - tuple (x, y, rotation)
        field - The field to place the piece in
    """
    x, y, rotation = placement
    for py, row in enumerate(PIECES[piece][rotation]):
        for px, block in enumerate(row):
            if block:
                field[y + py][x + px] = block


def is_harddrop_possible(piece, placement, field):
    """Determine if piece can be harddropped into a given position.
    
    Only checks piece in it's current rotation state (not spins, slides, or kicks).
    
    Args:
        piece - A piece in "ILOZTJS"
        placement - tuple (x, y, rotation)
        field - The field to test (in list form)
    Returns True if placement succeeded, False if not. Only modifies field if successful.
    """
    # test if non-empty columns are clear
    # test if spot where piece needs to go is clear
    # make sure piece is not floating
    x, y, rotation = placement
    floating = True
    # attempt to place piece, and determine if it is floating
    for py, row in enumerate(PIECES[piece][rotation]):
        for px, block in enumerate(row):
            if block:
                # check if piece inbounds (need to do this first so we don't get out of index error)
                if not (y + py >= 0 and 9 >= x + px >= 0):
                    return False
                # space is already occupied
                if field[y + py][x + px]:
                    return False
                # block is touching either bottom of the field or occupied space below it
                if floating and (y + py == 0 or field[y + py - 1][x + px]):
                    floating = False
    if floating:
        return False
    # make sure piece can be dropped into place by checking that columns above are clear
    # slice field above the top of the piece, then transpose into columns
    field_cols_above_piece = list(zip(*field[y + MAX_Y_OFFSET[piece][rotation]:20]))
    for col in OCCUPIED_COLS[piece][rotation]:
        # if any block exists in cols above the piece, fail
        if any(field_cols_above_piece[x + col]):
            return False
    return True


def main():
    #albatross without T piece
    test_field, _ = fumen.decode("v115@AhBtDewhQ4CeBti0whR4AeRpilg0whAeQ4AeRpglCe?whJeAgl")
    print(is_bag_possible(test_field, "SOLIZJ"))


if __name__ == "__main__":
    main()