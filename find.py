"""Find T-spin opener setups that end in a 3rd bag PC.

This will start as an extension to newjade's solution-finder and hopefully become a standalone utility.
Using: solution-finder-0.511
"""

import time
from sfinder import SFinder
from tet import TetOverlay, TetSetup, TetField
import gen, output
from tqdm import tqdm, TqdmSynchronisationWarning
import warnings
from copy import deepcopy


def is_TSS(solution, x, y, vertical_T=False):
    # for now, filter out solutions that use less than 6 pieces
    # (carrying over pieces into the next bag makes search space too large)

    # find # pieces by taking len of sequence str (all fumens should have same length)
    if len(solution.sequence) == 6:
        # leaving each solution's field modfied is by design
        # this way it's as if sfinder had found solutions with Ts already placed
        solution.field.add_T(x, y, vertical=vertical_T)
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


def get_TSS_continuations(field, rows, cols, bag_filter, TSS1, TSS2,
                          find_mirrors):
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
                            use_cache=True)
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
                            use_cache=True)

                    else:
                        tss2_sols = []
                    t.update()

                valid_sols = []
                if bag_filter == "isTSS-any":
                    # check if setup is actually a TSS (with all 7 pieces)
                    if TSS1:
                        valid_sols.extend(
                            filter(lambda sol: is_TSS(sol, col, row, vertical_T=False),
                                tss1_sols))
                        valid_sols.extend(
                            filter(
                                lambda sol: is_TSS(sol, col, row, vertical_T=True),
                                tss1_sols_copy))
                    if TSS2:
                        valid_sols.extend(
                            filter(lambda sol: is_TSS(sol, col, row, vertical_T=False),
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


def get_TSD_continuations(field, rows, cols, bag_filter, find_mirrors):
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
                        use_cache=True)

                    valid_sols = []
                    if bag_filter == "isTSD-any":
                        # check if setup is actually a TSS (with all 7 pieces)
                        valid_sols.extend(
                            filter(lambda sol: is_TSD(sol, col, row),
                                   tsd_sols))
                    else:
                        valid_sols.extend(tsd_sols)
                    solutions.extend(valid_sols)
                t.update()
    t.close()
    return solutions


def get_Tetris_continuations(field, row, cols):
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
                use_cache=True)
            solutions.extend(tet_sols)
    return solutions


def setups_from_input():
    # raise exception if input file not found? need a standard way of error handling for humans
    # allow changing of working-dir?
    timer_start = time.perf_counter()
    sf = SFinder()  # really should get rid of this
    pc_height = None  # need to refactor this (all the arg stuff)
    pc_cutoff = None
    with open("input.txt", "r") as input_file:
        bags = input_file.read().splitlines()

    setups = []  # do i need to initalize this?
    title = ""  #title/heading of output.html
    for i, bag in enumerate(bags):
        bag_args = bag.split(' ')
        setup_type = bag_args.pop(0)
        # defaults
        bag_rows = []
        bag_cols = []
        bag_filter = None
        for arg in bag_args:
            if arg[:3] == "col":
                if arg[4:] == "any":
                    # default for tspin, should be 0-9 for tetris
                    bag_cols = list(range(1, 8))
                else:
                    bag_cols = list(map(int, arg[4:].split(',')))
            if arg[:3] == "row":
                bag_rows = list(map(int, arg[4:].split(',')))
            if arg[:6] == "filter":
                bag_filter = arg[7:]
            if arg[:6] == "height":
                pc_height = arg[7:]
            if arg[:6] == "cutoff":
                pc_cutoff = float(arg[7:])

        if setup_type == "TSS-any":
            setup_func = lambda field: get_TSS_continuations(field, bag_rows, bag_cols, bag_filter, True, True, i > 0)
            bag_title = "TSS"
        elif setup_type == "TSS1":
            setup_func = lambda field: get_TSS_continuations(field, bag_rows, bag_cols, bag_filter, True, False, i > 0)
            bag_title = "TSS1"
        elif setup_type == "TSS2":
            setup_func = lambda field: get_TSS_continuations(field, bag_rows, bag_cols, bag_filter, False, True, i > 0)
            bag_title = "TSS2"
        elif setup_type == "TSD":
            setup_func = lambda field: get_TSD_continuations(field, bag_rows, bag_cols, bag_filter, i > 0)
            bag_title = "TSD"
        elif setup_type == "Tetris":
            # only supports 1 row for tetrises
            setup_func = lambda field: get_Tetris_continuations(field, bag_rows[0], bag_cols)
            bag_title = "Tetris"
        elif setup_type == "PC":
            print("Bag %d: Finding PCs..." % i)
            title += " -> PC"
            setups = list(
                filter(lambda setup: setup.find_PCs(sf, pc_height, pc_cutoff),
                       tqdm(setups, unit="setup")))
            print("")  #newline so tqdm output isn't weird
            break  # setup finding ends with a PC
        else:
            raise ValueError("Unknown setup type '%s'." % setup_type)

        if i == 0:
            print("Bag %d: Finding %s initial bag setups..." % (i, bag_title))
            title = bag_title
            setups = list(map(TetSetup, setup_func(TetField(from_list=[]))))
        else:
            print("Bag %d: Finding %s continuations..." % (i, bag_title))
            title += " -> " + bag_title
            for setup in tqdm(setups, unit="setup"):
                conts = setup_func(setup.solution.field)
                setup.add_continuations(conts)
            # remove setups with no continuations
            setups = [
                setup for setup in setups if len(setup.continuations) > 0
            ]
        #extra newline to make room for extra tqdm bar
        print("\nBag %d: Found %d valid setups" % (i, len(setups)))

    print("Generating output file...")
    # image height is hardcoded for now (can I do something like determine max height at each step?)
    output.output_results(
        sorted(setups, key=(lambda s: s.PC_rate), reverse=True), title,
        pc_cutoff, pc_height, "7")
    print("Done.", end=' ')
    print("(Total elapsed time: %.2fsec)" %
          (time.perf_counter() - timer_start))


def main():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", TqdmSynchronisationWarning)
        setups_from_input()


if __name__ == '__main__':
    main()
