"""Find setups using lower-level modules.

The finder module is intended to be used by scripts to run any setup finding code.
Input and output should be done by the scripts themselves and then passed into and received from the finder module."""

from copy import deepcopy
from tqdm import tqdm
from setupfinder.finder.sfinder import SFinder
from setupfinder.finder.tet import TetOverlay, TetSetup, TetField
from setupfinder.finder import gen


def is_TSS(solution, x, y, vertical_T=False, mirror=False):
    # for now, filter out solutions that use less than 6 pieces
    # (carrying over pieces into the next bag makes search space too large)

    if len(solution.sequence) == 6:
        # leaving each solution's field modfied is by design
        # this way it's as if sfinder had found solutions with Ts already placed
        solution.field.add_T(x, y, vertical=vertical_T, mirror=mirror)
        # todo: (maybe I should move addT to TetSolution?)
        solution.sequence += "T"
        return solution.field.clearedRows == 1
    else:
        return False


def is_TSD(solution, x, y):
    if len(solution.sequence) == 6:
        solution.field.add_T(x, y, False)  #flat T
        solution.sequence += "T"
        return solution.field.clearedRows == 2
    else:
        return False


def test_TSD(solution, x, y):
    """Test if solution _would_ be a TSD, don't actually add the T piece like isTSD."""
    sol = deepcopy(solution)
    sol.field.add_T(x, y, False)  #flat T
    return sol.field.clearedRows == 2


def is_TST(solution, x, y, mirror):
    if len(solution.sequence) == 6:
        #vertical T, flipped in comparison to TSS vertical T
        solution.field.add_T(
            x - 1 if mirror else x + 1, y, True, mirror=not mirror)
        solution.sequence += "T"
        return solution.field.clearedRows == 3
    else:
        return False


def get_TSS_continuations(field,
                          rows,
                          cols,
                          bag_filter,
                          TSS1,
                          TSS2,
                          find_mirrors,
                          use_cache=None):
    """Finds TSS continuations. Set TSS1 and TSS2 variables to choose which type.
    Find mirrors should be used to find setups with both left and right overhangs."""
    sf = SFinder()
    solutions = []
    mirrors = [False, True] if find_mirrors else [False]
    # manual tqdm progress bar
    t = tqdm(
        total=len(rows) * len(cols) * (2
                                       if TSS1 and TSS2 else 1) * len(mirrors),
        unit="setup")
    for row in rows:
        for col in cols:
            for mirror in mirrors:
                # make copies to avoid mutating field
                if TSS1:
                    tss1_field = deepcopy(field)
                    # 6 is a reasonable height for blank field setups (7+ should be impossible in one bag)
                    # may want to have an option for different heights for finding tspins in other bags (prob pass an arg)
                    if tss1_field.add_overlay(
                            gen.generate_TSS1(6, col, row, mirror)):
                        tss1_sols = sf.setup(
                            fumen=gen.output_fumen(tss1_field.field),
                            use_cache=use_cache)
                        # copy so we can try both flat and vertical T
                    else:
                        tss1_sols = []
                    t.update()
                    tss1_sols_copy = deepcopy(tss1_sols)
                if TSS2:
                    tss2_field = deepcopy(field)
                    if tss2_field.add_overlay(
                            gen.generate_TSS2(6, col, row, mirror)):
                        tss2_sols = sf.setup(
                            fumen=gen.output_fumen(tss2_field.field),
                            use_cache=use_cache)

                    else:
                        tss2_sols = []
                    t.update()

                valid_sols = []
                if bag_filter == "isTSS-any":
                    # check if setup is actually a TSS (with all 7 pieces)
                    if TSS1:
                        valid_sols.extend(
                            filter(lambda sol: is_TSS(sol, col, row, vertical_T=False, mirror=mirror),
                                tss1_sols))
                        valid_sols.extend(
                            filter(
                                lambda sol: is_TSS(sol, col, row, vertical_T=True, mirror=mirror),
                                tss1_sols_copy))
                    if TSS2:
                        valid_sols.extend(
                            filter(lambda sol: is_TSS(sol, col, row, vertical_T=False, mirror=mirror),
                                tss2_sols))
                else:
                    if TSS1:
                        valid_sols.extend(tss1_sols)
                    if TSS2:
                        valid_sols.extend(tss2_sols)
                #if VERBOSE (todo: add something like this?)
                #print("  Found %d valid TSS setups at %d,%d" % (len(valid_sols), col, row))
                solutions.extend(valid_sols)
    t.close()
    return solutions


def get_TSD_continuations(field,
                          rows,
                          cols,
                          bag_filter,
                          find_mirrors,
                          use_cache=None):
    sf = SFinder()
    solutions = []
    mirrors = [False, True] if find_mirrors else [False]
    # manual tqdm progress bar
    t = tqdm(total=len(rows) * len(cols) * len(mirrors), unit="setup")
    for row in rows:
        for col in cols:
            for mirror in mirrors:
                # make copies to avoid mutating field
                tsd_field = deepcopy(field)
                if tsd_field.add_overlay(
                        gen.generate_TSD(6, col, row, mirror)):
                    tsd_sols = sf.setup(
                        fumen=gen.output_fumen(tsd_field.field),
                        use_cache=use_cache)

                    valid_sols = []
                    if bag_filter == "isTSD-any":
                        valid_sols.extend(
                            filter(lambda sol: is_TSD(sol, col, row),
                                   tsd_sols))
                    elif bag_filter == "testTSD":
                        valid_sols.extend(
                            filter(lambda sol: test_TSD(sol, col, row),
                                   tsd_sols))
                    else:
                        valid_sols.extend(tsd_sols)
                    solutions.extend(valid_sols)
                t.update()
    t.close()
    return solutions


def get_TST_continuations(field,
                          rows,
                          cols,
                          bag_filter,
                          find_mirrors,
                          use_cache=None):
    sf = SFinder()
    solutions = []
    mirrors = [False, True] if find_mirrors else [False]
    # manual tqdm progress bar
    t = tqdm(total=len(rows) * len(cols) * len(mirrors), unit="setup")
    for row in rows:
        for col in cols:
            for mirror in mirrors:
                # make copies to avoid mutating field
                tst_field = deepcopy(field)
                if tst_field.add_overlay(
                        gen.generate_TST(6, col, row, mirror)):
                    tst_sols = sf.setup(
                        fumen=gen.output_fumen(tst_field.field),
                        use_cache=use_cache)

                    #sf.setup returns None if setup would require too many pieces
                    if tst_sols is not None:
                        valid_sols = []
                        if bag_filter == "isTST":
                            valid_sols.extend(
                                filter(
                                    lambda sol: is_TST(sol, col, row, mirror),
                                    tst_sols))
                        else:
                            valid_sols.extend(tst_sols)
                        solutions.extend(valid_sols)
                t.update()
    t.close()
    return solutions


def get_Tetris_continuations(field, row, cols, use_cache=None):
    sf = SFinder()
    solutions = []
    for col in cols:
        # make copies to avoid mutating field
        tet_field = deepcopy(field)
        # this height should be passed in (from input file?)
        tet_overlay = gen.generate_Tetris(7, col, row)
        if tet_field.add_overlay(tet_overlay):
            tet_sols = sf.setup(
                fumen=gen.output_fumen(
                    tet_field.field, comment="-m o -f i -p *p7"),
                use_cache=use_cache)
            solutions.extend(tet_sols)
    return solutions


def get_setup_func(setup_type, rows, cols, setup_filter, mirrors, setup_cache):
    """Return a function that can be applied to a field argument to find setups of the proper type."""
    if setup_type == "TSS-any" or setup_type == "TSS":
        return lambda field: get_TSS_continuations(field, rows, cols, setup_filter, True, True, mirrors, use_cache=setup_cache)
    elif setup_type == "TSS1":
        return lambda field: get_TSS_continuations(field, rows, cols, setup_filter, True, False, mirrors, use_cache=setup_cache)
    elif setup_type == "TSS2":
        return lambda field: get_TSS_continuations(field, rows, cols, setup_filter, False, True, mirrors, use_cache=setup_cache)
    elif setup_type == "TSD-any" or setup_type == "TSD":
        return lambda field: get_TSD_continuations(field, rows, cols, setup_filter, mirrors, use_cache=setup_cache)
    elif setup_type == "TST":
        return lambda field: get_TST_continuations(field, rows, cols, setup_filter, mirrors, use_cache=setup_cache)
    elif setup_type == "Tetris":
        # only supports 1 row for tetrises
        return lambda field: get_Tetris_continuations(field, rows[0], cols, use_cache=setup_cache)
    else:
        raise ValueError("Unknown setup type '%s'." % setup_type)

def find_initial_setups(setup_func):
    """Apply setup function to blank field to get initial bag 'continuations.'"""
    return list(map(TetSetup, setup_func(TetField(from_list=[]))))