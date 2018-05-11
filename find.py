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


def find_continuations(sols, overlay):
    """Find continuations for a list of solutions using an overlay. Returns a list of TetSetups."""
    # todo: need to make sure different invocations of sfinder respect working_path if it is set differently
    sf = SFinder()
    # filter out solutions where adding overlay isn't possible (eg. filled block where it must be unfilled)
    # use list here so printing doesn't consume the filter
    filtered_setups = list(
        map(TetSetup, filter(lambda sol: sol.add_overlay(overlay), sols)))
    print(
        "%d setups have potential continuations. Finding continuation setups..."
        % len(filtered_setups))
    # find continuations for each sol with tqdm progress bar, then add them as continuations to each setup, filtering setups without results
    return list(filter(lambda setup: setup.add_continuations(sf.setup(fumen=setup.get_fumen("-m o -f i -p *p7"), use_cache=True)), tqdm(filtered_setups, unit="setup")))


def find_TSS_Tetris_PC():
    """Find setups that start with a TSS and end with a Tetris+PC.
    
    This is an example of how to use setup-finder to find multi-bag setups. Hopefully it is a good enough
    starting off point to apply to other problems.

    First we find first bag solutions, using sf.setup and a fumen input, then filter them using is_TSS.
    Later on, setup-finder will generate all possible TSS setups (or even have solutions pre-generated somewhere),
    so you won't have to manually create a fumen for each T position.

    Next, we import an overlay and find continuations for all the bag 1 setups we found.
    Eventually you'll be able to specify what you are trying to do in some sort of input file, and overlays
    will be able to be specified there in text form as below or in fumen form.
    Also, you should be able to generate Tspin/Tetris overlays to find all possible attacking continuations.

    Lastly, we find PCs and print results sorted by PC rate. Since PCs will always be the "end" of a setup
    in the sense that you end up with a blank field, they are treated differently than continuations.
    (Todo: For setups that start AFTER a PC in the middle of a bag, maybe I should have a setting to find these.)
    Later on, you should be able to find setups that don't end on a PC that are scored and sorted differently,
    for example by the success rate per piece sequence, or by the average key presses used. PCs should also be
    weighted based on what piece sequences they can be stacked by (or the minimum number of setups to learn to get
    the desired success rate.)
    """
    pc_cutoff = 80.0
    with warnings.catch_warnings():
        warnings.simplefilter(
            "ignore",
            TqdmSynchronisationWarning)  #annoying tqdm bug workaround

        sf = SFinder()
        print("Working dir: %s" % sf.working_dir)
        timer_start = time.perf_counter()

        print("Bag 1: Finding row 2 TSS1 setups...")
        bag1_sols = []
        for x in range(1, 8):  #only 1-7 are possible
            tss_fumen = gen.output_fumen(gen.generate_TSS1(6, x, 2))
            tss_sols = sf.setup(fumen=tss_fumen, use_cache=True)
            print("  Found %d solutions with possible TSS at %d, 2" %
                  (len(tss_sols), x))
            #deepcopy because issTSS changes sols, want a copy to spin T differently with
            tss_sols_copy = deepcopy(tss_sols)
            valid_sols = list(
                filter(lambda sol: is_TSS(sol, x, 2, vertical_T=False),
                       tss_sols))
            valid_sols.extend(
                filter(lambda sol: is_TSS(sol, x, 2, vertical_T=True),
                       tss_sols_copy))
            print("  Found %d valid TSS setups at %d, 2" % (len(valid_sols),
                                                            x))
            bag1_sols.extend(valid_sols)
        print(
            "Bag 1: Found %d total valid TSS setups" % len(bag1_sols), end=' ')
        print("(Elapsed time: %.2fsec)" % (time.perf_counter() - timer_start))
        print("Bag 2: Finding continuations with overlay...")
        overlay = TetOverlay("""........._
                                ........._
                                ........._
                                *********_
                                *********_
                                *********_
                                *********_""")
        setups = find_continuations(bag1_sols, overlay)
        num_continuations = sum(
            map(lambda setup: len(setup.continuations), setups))
        print(
            "Bag 2: Found %d setups with %d valid continuations" %
            (len(setups), num_continuations),
            end=' ')
        print("(Elapsed time: %.2fsec)" % (time.perf_counter() - timer_start))

        print("Bag 3: Finding PCs...")
        # manually added height here - I should calculate this from cleared rows and be able to specify that I'm going for an 8 highpi
        pc_setups = list(
            filter(lambda setup: setup.find_PCs(sf, 7, pc_cutoff),
                   tqdm(setups, unit="setup")))
        print(
            "Bag 3: Found %d setups with PC success greater than %.2f%%, outputting to output.html"
            % (len(pc_setups), pc_cutoff),
            end=' ')
        print("(Total elapsed time: %.2fsec)" %
              (time.perf_counter() - timer_start))

    # dominate has problems rendering → or I would use that, need to find workaround
    print("Generating output file...")
    output.output_results(
        sorted(pc_setups, key=(lambda s: s.PC_rate), reverse=True),
        "Row 1 TSS2 -> Tetris -> PC", pc_cutoff)


def get_TSS_continuations(field,
                          rows,
                          cols,
                          bag_filter,
                          TSS1=False,
                          TSS2=False):
    """field is a TetField"""
    sf = SFinder()
    solutions = []
    for row in rows:
        for col in cols:
            # make copies to avoid mutating field
            if TSS1:
                tss1_field = deepcopy(field)
                # 6 is a reasonable height for blank field setups (7+ should be impossible in one bag)
                # may want to have an option for different heights for finding tspins in other bags (prob pass an arg)
                tss1_field.add_overlay(gen.generate_TSS1(6, col, row))
                tss1_sols = sf.setup(
                    fumen=gen.output_fumen(tss1_field.field), use_cache=True)
                # copy so we can try both flat and vertical T
                tss1_sols_copy = deepcopy(tss1_sols)
            if TSS2:
                tss2_field = deepcopy(field)
                tss2_field.add_overlay(gen.generate_TSS2(6, col, row))
                tss2_sols = sf.setup(
                    fumen=gen.output_fumen(tss2_field.field), use_cache=True)

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
            #print("  Found %d valid TSS setups at %d,%d" % (len(valid_sols),
            #                                                col, row))
            solutions.extend(valid_sols)
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
                pc_height = int(arg[7:])
            if arg[:6] == "cutoff":
                pc_cutoff = float(arg[7:])

        if setup_type == "TSS-any":
            if i == 0:
                print("Bag %d: Finding TSS initial bag setups..." % i)
                title = "TSS"
                setups = list(
                    map(TetSetup,
                        get_TSS_continuations(
                            TetField(from_list=[]),
                            bag_rows,
                            bag_cols,
                            bag_filter,
                            True,
                            True)))
            else:
                raise NotImplementedError(
                    "fix this - tspins only work for 1st bag")
        elif setup_type == "TSS1":
            raise NotImplementedError("Bag %d: %s not yet implemented" %
                                      (i, setup_type))
        elif setup_type == "TSS2":
            raise NotImplementedError("Bag %d: %s not yet implemented" %
                                      (i, setup_type))
        elif setup_type == "TSD":
            raise NotImplementedError("Bag %d: %s not yet implemented" %
                                      (i, setup_type))
        elif setup_type == "Tetris":
            if i > 0:
                print("Bag %d: Finding Tetris continuations..." % i)
                title += " -> Tetris"
                for setup in setups:
                    # only supports 1 row for tetrises
                    conts = get_Tetris_continuations(setup.solution.field,
                                                     bag_rows[0], bag_cols)
                    setup.add_continuations(conts)
            else:
                raise NotImplementedError(
                    "Initial bag Tetris not implemented.")
        elif setup_type == "PC":
            print("Bag %d: Finding PCs..." % i)
            title += " -> PC"
            setups = list(
                filter(lambda setup: setup.find_PCs(sf, pc_height, pc_cutoff),
                       tqdm(setups, unit="setup")))
            print("")  #newline so tqdm output isn't weird
        else:
            raise ValueError("Unknown setup type '%s'." % setup_type)

        if i > 0:
            # remove setups with no continuations
            setups = [
                setup for setup in setups if len(setup.continuations) > 0
            ]
        print("Bag %d: Found %d valid setups" % (i, len(setups)))
    print("Generating output file...")
    output.output_results(
        sorted(setups, key=(lambda s: s.PC_rate), reverse=True), title,
        pc_cutoff)
    print("Done.", end=' ')
    print("(Total elapsed time: %.2fsec)" %
          (time.perf_counter() - timer_start))


def main():
    setups_from_input()


if __name__ == '__main__':
    main()
