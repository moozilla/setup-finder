"""Tests for the analysis module."""

import pytest
import setupfinder.analysis
from setupfinder.finder import fumen


@pytest.fixture(scope="module")
def fields():
    """Return a list of fields to be tested by unit tests."""
    test_fumens = [
        "v115@AhBtDewhQ4ywBti0whR4wwRpilg0whAeQ4AeRpglCe?whJeAgl",  #albatross
        "v115@hghlQ4BeAtEeglR4BtAewhh0AeglA8Q4AtRpwhg0Be?D8Rpwhg0CeE8whB8AeI8AeG8JeAgH",  #DT-cannon bag2
        "v115@AhBtDewhQ4CeBti0whR4AeRpilg0whAeQ4AeRpglCe?whJeAgl",  #albatross without T
    ]
    return [fumen.decode(test_fumen)[0] for test_fumen in test_fumens]


def test_find_placements(fields):
    """Unit test for find_placements."""
    for test_field in fields:
        field_height = len(test_field)
        piece_locations = setupfinder.analysis.find_placements(test_field)
        assert len(piece_locations) == 7
        for piece in "ILOZTJS":
            assert piece in piece_locations
            # make sure piece is either None or valid location
            if piece_locations[piece] is not None:
                x, y, rot = piece_locations[piece]
                # make sure coords are valid, +/-2 from actual bounds because blank parts of pieces
                # can be out-of-bounds and piece still in-bounds
                # this doesn't check if each piece is actually in bounds (presumably check_piece_at should do that)
                assert -2 <= x <= 11
                assert -2 <= y <= field_height + 2
                assert 0 <= rot <= 3
                if piece == "O":
                    # O should always be spawn rotated
                    assert rot == 2


def test_find_placement(fields):
    """Unit test for find_placement."""
    test_field = fields[0]
    l_loc = setupfinder.analysis.find_placement("L", test_field)
    assert l_loc == (5, 0, 0)


def test_is_harddrop_possible():
    """ Unit tests for is_harddrop_possible.
    successes:
        for each placement, dropping onto blank ground in every position possible for that piece
        dropping onto ground raised a certain amount
        ground where only one point of piece makes contact:
            v115@CgywHewwA8ZeQ4BeQ4FeR4AeR4AezhA8Q4BeQ4DeA8?DeA8ieAgl
        dropping inbetween narrow gap:
        v115@1gB8CeA8AeA8BeB8CeA8whA8Q4AeB8CeA8whA8R4B8?AewwAeA8whA8AeQ4B8ywA8whA8JeAgl
    fails:
        piece out of bounds
        part of piece occupied
        floating pieces (test if bottom block in column makes contact for each column)
         (note: this wouldnt work with more complex shapes, but should work with every mino?)
        gap too narrow, or overhang above (for later: argument for height harddropped from)
    """
    # attempt to place every piece/rotation in every possible spot on a blank field
    # should succeed for all in-bounds pieces, should fail for out-of-bounds
    blank_field = [[0] * 10 for __ in range(20)]
    for piece in "ILOZTJS":
        for rot in range(4):
            for y in range(-2, 0):
                for x in range(-2, 10):
                    result = setupfinder.analysis.is_harddrop_possible(piece, (x, y, rot), blank_field)
                    if x in list(setupfinder.analysis.VALID_X_PLACEMENTS[piece]
                                 [rot]) and y == setupfinder.analysis.MIN_Y_PLACEMENT[piece][rot]:
                        assert result == True
                    else:
                        assert result == False

    # test piece hanging off a single point, also hanging from the middle row of the piece
    # one floating dot at 5,2
    test_field, __ = fumen.decode("v115@MhA8heAgH")
    for __ in range(20 - len(test_field)):
        test_field.append([0] * 10)
    supported_placements = [("I", (2, 2, 0)), ("I", (3, 3, 1)), ("L", (3, 2, 0))]
    floating_placements = [("I", (1, 2, 0)), ("I", (2, 3, 1)), ("L", (3, 3, 0))]
    for piece, placement in supported_placements:
        assert setupfinder.analysis.is_harddrop_possible(piece, placement, test_field) == True
    for piece, placement in floating_placements:
        assert setupfinder.analysis.is_harddrop_possible(piece, placement, test_field) == False

    # test harddropping into narrow gap
    # x = 0 is 3-wide, x = 4 is 2-wide, x = 7 is 1-wide
    test_field, __ = fumen.decode("v115@AhA8BeA8AeB8CeA8BeA8AeB8CeA8BeA8AeB8CeA8Be?A8AeB8JeAgH")
    for __ in range(20 - len(test_field)):
        test_field.append([0] * 10)
    # test every piece/rotation in each spot
    # OCCUPIED_COLS is set up the same way as PIECES, for each rotation it's a list of which cols contain a block
    for piece, rot_cols in setupfinder.analysis.OCCUPIED_COLS.items():
        for rotation, cols in enumerate(rot_cols):
            rotation_width = len(cols)
            # first column with a block in it (to align piece)
            rotation_x_offset = cols[0]
            # bottom of the piece so we don't try placing out of bounds
            rotation_y = setupfinder.analysis.MIN_Y_PLACEMENT[piece][rotation]
            fits_in_3_wide_gap = setupfinder.analysis.is_harddrop_possible(
                piece, (0 - rotation_x_offset, rotation_y, rotation), test_field)
            fits_in_2_wide_gap = setupfinder.analysis.is_harddrop_possible(
                piece, (4 - rotation_x_offset, rotation_y, rotation), test_field)
            fits_in_1_wide_gap = setupfinder.analysis.is_harddrop_possible(
                piece, (7 - rotation_x_offset, rotation_y, rotation), test_field)
            assert fits_in_3_wide_gap == (rotation_width <= 3)
            assert fits_in_2_wide_gap == (rotation_width <= 2)
            assert fits_in_1_wide_gap == (rotation_width <= 1)

    # test places where piece fits but spot covered
    # same field as before but entire thing is covered
    test_field, __ = fumen.decode("v115@zgJ8CeA8BeA8AeB8CeA8BeA8AeB8CeA8BeA8AeB8Ce?A8BeA8AeB8JeAgH")
    for __ in range(20 - len(test_field)):
        test_field.append([0] * 10)
    for piece, rot_cols in setupfinder.analysis.OCCUPIED_COLS.items():
        for rotation, cols in enumerate(rot_cols):
            # first column with a block in it (to align piece)
            rotation_x_offset = cols[0]
            # bottom of the piece so we don't try placing out of bounds
            rotation_y = setupfinder.analysis.MIN_Y_PLACEMENT[piece][rotation]
            covered_3_wide_gap = setupfinder.analysis.is_harddrop_possible(
                piece, (0 - rotation_x_offset, rotation_y, rotation), test_field)
            assert covered_3_wide_gap == False

    # make sure flat i piece can't be placed with blocks covering row 1
    # (this tests covering blocks inside the piece's bounding box)
    test_field, __ = fumen.decode("v115@RhJ8DeF8JeAgl")
    for __ in range(20 - len(test_field)):
        test_field.append([0] * 10)
    covered_i_piece = setupfinder.analysis.is_harddrop_possible("I", (0, -1, 0), test_field)
    assert covered_i_piece == False


def test_place_piece():
    """Unit test for place_piece."""
    # should result in PC setup
    test_placements = [("J", (7, -1, 2)), ("S", (1, -1, 2)), ("O", (8, 1, 2)), ("L", (7, 2, 0)), ("I", (4, 0, 1)),
                       ("T", (-1, 0, 1)), ("Z", (0, 1, 2))]
    field = [[0] * 10 for __ in range(20)]
    for piece, placement in test_placements:
        setupfinder.analysis.place_piece(piece, placement, field)
    encoded_field = fumen.encode([(field, "")])
    assert encoded_field == "v115@9gBtDewhilwwBtCewhglRpxwR4Bewhg0RpwwR4Cewh?i0JeAgH"


def test_is_bag_possible(fields):
    """Unit test is_bag_possible.
     
    Note: hold is not tested here, it should be tested in bag_coverage instead
    """
    test_field = fields[2]  # albatross without T
    # should work with only harddrop
    for bag in ["SOLIZJ", "OSILJZ", "ILJOZS"]:
        assert setupfinder.analysis.is_bag_possible(test_field, bag) == True
    # fail with only harddrop, would work with hold
    for bag in ["SZOLJI", "OSIJLZ", "ILJSZO"]:
        assert setupfinder.analysis.is_bag_possible(test_field, bag) == False
    # should work with hold
    #for bag in ["SZOLJI", "OSIJLZ", "ILJSZO"]:
    #    assert setupfinder.analysis.is_bag_possible(test_field, bag, hold=True) == True


def test_bag_coverage(fields):
    """Unit test for bag_coverage."""
    test_field = fields[2]  # albatross without T
    coverage = setupfinder.analysis.bag_coverage(test_field, pieces="ILOZJS")
    hold_coverage = setupfinder.analysis.bag_coverage(test_field, pieces="ILOZJS", hold=True)
    mirror_coverage = setupfinder.analysis.bag_coverage(test_field, pieces="ILOZJS", hold=True, mirror=True)
    assert coverage[0] < hold_coverage[0] < mirror_coverage[0]
    assert coverage[1] == hold_coverage[1] == mirror_coverage[1]


def test_find_hold_equivalent_bags():
    """Unit test for find_hold_equivalent_bags."""
    assert setupfinder.analysis.find_hold_equivalent_bags("STZ") == {'TZS', 'SZT', 'TSZ', 'STZ'}


def test_mirrored(fields):
    """Unit test for mirrored."""
    mirror_dt = fumen.encode([(setupfinder.analysis.mirrored(fields[1]), "")])
    mirror_alb = fumen.encode([(setupfinder.analysis.mirrored(fields[2]), "")])
    assert mirror_dt == "v115@hgQ4BeAth0BewhAeR4Btg0CewhRpQ4AtA8g0Aehlwh?RpD8BeglwhE8CeglG8AeI8AeB8JeAgH"
    assert mirror_alb == "v115@9gwhDeR4CewhilR4CeAtwhgli0RpAeBtwhCeg0RpAe?AtKeAgH"
