"""Perform deeper analysis of setups.

This module is intended to be used in conjunction with the finder module. It will contain methods that:
* Determine what bags can be used to build a setup
* Find the specific keypresses/finesses used to perform a setup
* Score a setup based on completion percent or keypresses used
  (or est. time to complete taking into account various delays)
* From a list of setups, find a minimal system that covers 100% of bags and score overall system
"""

from copy import deepcopy
from itertools import permutations
# these 4 are temporary, should be refactored out
import gzip
import pickle
from pathlib import Path
from tqdm import tqdm
#
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

PIECE_SIZE = {'I': 4, 'L': 3, 'O': 2, 'Z': 3, 'T': 3, 'J': 3, 'S': 3}


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
    # this list will determine what y-value to start cols above the piece (for checking if piece can be dropped in)
    highest_block = [0] * PIECE_SIZE[piece]
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
                highest_block[px] = y + py
    if floating:
        return False
    # make sure piece can be dropped into place by checking that columns above are clear
    field_cols = list(zip(*field))
    for col in OCCUPIED_COLS[piece][rotation]:
        # if any block exists in cols above the piece, fail
        # slice col 1 above the highest piece block in that column
        if any(field_cols[x + col][highest_block[col] + 1:]):
            return False
    return True


def is_bag_possible(field, bag):
    """Determine if it's possible to perform setup with a particular bag.

    For now this tests only if pieces can be harddropped in, with no hold.

    Args:
        field - in list form like other functions in this module
        bag - string of pieces in order, eg. "TSOLIZJ"
    Returns True or False
    """
    placements = find_placements(field)
    # strip all non-gray blocks from field
    new_field = [[8 if block == 8 else 0 for block in row] for row in field]
    # extend field height to 20
    for __ in range(20 - len(new_field)):
        new_field.append([0] * 10)
    for piece in bag:
        # got a piece that isn't specified in field
        if not placements[piece]:
            return False
        if not is_harddrop_possible(piece, placements[piece], new_field):
            return False
        else:
            # place piece into new_field
            place_piece(piece, placements[piece], new_field)
    return True


def hold_equivalent_bags(bag, held_piece=""):
    """Return a set of bags that can be used to place pieces in a particular order using hold.
    
    Args:
        bag - string of pieces (eg. "IOSTL")
        held_piece - piece currently in hold
    Returns:
        set containing all possible bags that bag can be transformed into using hold
    """
    # base case, return held piece if it exists
    if not bag:
        if held_piece:
            return [held_piece]
        else:
            return [""]
    # find results for if hold is used and if not, and return union of these
    hold_result = hold_equivalent_bags(bag[1:], bag[0])
    no_hold_result = hold_equivalent_bags(bag[1:], held_piece)
    return set(held_piece + result for result in hold_result) | set(bag[0] + result for result in no_hold_result)


def mirrored(field):
    """Return a mirrored version of field.

    This swaps rows from left-right and also swaps L/J and S/Z blocks.
    Args:
        field - Field in list-form
    Returns:
        Mirrored field in list-form
    """
    mirror_colors = [0, 1, 6, 3, 7, 5, 2, 4, 8]
    return [[mirror_colors[block] for block in reversed(row)] for row in field]


def bag_coverage(field, bags, hold=False, mirror=False, tspin=False):
    """Determine what bags can be used to complete given setup.

    Note: this uses sets instead of lists to avoid duplicate sequences at each step

    Args:
        field - The setup specified in list form.
        bags - list of strings, which bags should be testsed
        (hold) - should bags that are equivalent under hold be counted?
        (mirror) - should bags that can be completed in mirrored form be counted?
        (tspin) - force T piece to come last (for tspin)
    Returns:
        list of bags
    """
    if tspin:
        holdless_bags = {
            bag
            for bag in bags if bag[-1] == "T" and is_bag_possible(field, bag[:-1]) or (
                mirror and is_bag_possible(mirrored(field), bag[:-1]))
        }
    else:
        holdless_bags = {
            bag
            for bag in bags if is_bag_possible(field, bag) or (mirror and is_bag_possible(mirrored(field), bag))
        }
    if not hold:
        return holdless_bags
    # out of remaining bags, find bags that work with hold if intersection of bags that work without hold
    # and bags equivalent to the bag being tested is not null
    hold_bags = {bag for bag in (bags - holdless_bags) if holdless_bags & hold_equivalent_bags(bag)}
    return holdless_bags | hold_bags


def all_bags(sequence):
    """Return a list of all possible permutations of a given piece sequence."""
    return {''.join(p) for p in permutations(sequence)}


def systematize(setups):
    """Return minimal set of setups that covers all possible bags with the best possible PC rate.

    Note: for now, each setup in setups should only have continuations 1 deep, so it will work for
          things like TSD->TSD->PC but not TSD->TSD->TSD->PC
          Also not set up for testTSD yet

    Args:
        setups - list of TetSetups as return by finder, doesn't need to be sorted
    Returns:
        list of tuples of (setup, score) where score is coverage*PC_rate
    """
    setup = setups[0]
    bags = all_bags("IOTLJSZ")
    """ coverages = []
    for cont in tqdm(setup.continuations):
        # get field and pieces from fumen, pieces shouldn't include T for tspin ones
        field, __ = fumen.decode(cont.solution.fumen)
        # don't mirror because it's not an initial bag
        # will have to somehow store isTSpin in TetSetup for using in tspin=True arg
        # should also have an option for Tetris...
        coverage = bag_coverage(field, bags, hold=True, tspin=True)
        coverages.append(coverage)
        #adjusted_PC_rate = (len(coverage) * cont.PC_rate) / len(bags)
        #print(f"{cont.solution.fumen}: {len(coverage)}/{len(bags)} bags, adj. PC rate: {adjusted_PC_rate:.2f}") """
    covered_bags = set()
    total_pc_rate = 0
    for i, cont in enumerate(setup.continuations):
        field, __ = fumen.decode(cont.solution.fumen)
        coverage = bag_coverage(field, bags - covered_bags, hold=True, tspin=True)
        new_bags = len(coverage - covered_bags)
        covered_bags = covered_bags | coverage
        total_pc_rate += new_bags * cont.PC_rate
        print(
            f"Adding {new_bags} new bags @ {cont.PC_rate}% - total {len(covered_bags)}/{len(bags)} = {total_pc_rate/len(bags):.2f}%"
        )


def main():
    """ #albatross without T piece
    test_field, __ = fumen.decode("v115@AhBtDewhQ4CeBti0whR4AeRpilg0whAeQ4AeRpglCe?whJeAgl")
    bags = all_bags("ILOZJS")
    print(len(bag_coverage(test_field, bags)))
    print(len(bag_coverage(test_field, bags, hold=True)))
    print(len(bag_coverage(test_field, bags, hold=True, mirror=True)))
    print(len(bag_coverage(test_field, bags, hold=False, mirror=True))) """
    test_file = Path("output/test.bin")  #saved TSD->TSD->PC results
    # this part should be abstracted to some other module so i dont have to import gzip/pickle here?
    with gzip.open(test_file) as f:
        test_finder = pickle.load(f)
    setups = sorted(test_finder.setups, key=(lambda s: s.PC_rate), reverse=True)
    systematize(setups)


if __name__ == "__main__":
    main()