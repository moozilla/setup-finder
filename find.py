"""Find T-spin opener setups that end in a 3rd bag PC.

This will start as an extension to newjade's solution-finder and hopefully become a standalone utility.
Using: solution-finder-0.511
"""

import time
from sfinder import SFinder
from tet import TetOverlay, TetSetup


def isTSS(solution, verticalT=False):
    # for now, filter out solutions that use less than 6 pieces
    # (carrying over pieces into the next bag makes search space too large)

    # find # pieces by taking len of sequence str (all fumens should have same length)
    if len(solution.sequence) == 6:
        # leaving each solution's field modfied is by design
        # this way it's as if sfinder had found solutions with Ts already placed
        solution.field.addT(2, 2, vertical=verticalT)
        # todo: (maybe I should move addT to TetSolution?)
        solution.sequence += "T"
        return solution.field.clearedRows == 1
    else:
        return False


def findContinuationsWithOverlay(sols, overlay):
    """Takes a list of TetSolutions, returns a list of TetSetups"""
    # need to make sure different invocations of sfinder respect working_path if it is set differently
    sf = SFinder()
    valid_overlays = list(
        map(TetSetup, filter(lambda sol: sol.addOverlay(overlay), sols)))
    print("Found %d valid overlays" % len(valid_overlays))
    return list(filter(lambda setup: setup.addContinuations(sf.setup(input_diagram=setup.solution.field.tostring())), valid_overlays))


def findTSSTetrisPC():
    """Find setups that start with a TSS and end with a Tetris+PC.
    
    This is an example of how to use setup-finder to find multi-bag setups. Hopefully it is a good enough
    starting off point to apply to other problems.

    First we find first bag solutions, using sf.setup and a fumen input, then filter them using isTSS.
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
    sf = SFinder()
    print("Working dir: %s" % sf.working_dir)
    timer_start = time.perf_counter()

    print("Bag 1: Finding TSS setups...")
    bag1_sols = sf.setup(
        fumen=
        "v115@pgQpBeXpBeXpBewhWpCeVpxhAe2hZpJeAgWkAtD98A?wG98AwzVTASocTASodOEFbcRAVDEHBleEHBEoA6A",
        useCache=True)
    print("Found %d solutions with possible TSS at 2,2" % len(bag1_sols))
    valid_sols = list(
        filter(lambda sol: isTSS(sol, verticalT=True), bag1_sols))
    print("Bag 1: Found %d total valid TSS setups" % len(valid_sols), end=' ')
    print("(Elapsed time: %.2fsec)" % (time.perf_counter() - timer_start))
    print("Bag 2: Finding continuations with overlay...")
    overlay = TetOverlay("""*........_
                            *........_
                            *........_
                            *********_
                            *********_
                            *********_
                            *********_""")
    setups = findContinuationsWithOverlay(valid_sols, overlay)
    print(
        "Bag 2: Found %d setups with valid continuations" % len(setups),
        end=' ')
    print("(Elapsed time: %.2fsec)" % (time.perf_counter() - timer_start))

    print("Bag 3: Finding PCs...")
    pc_setups = list(filter(lambda setup: setup.findPCs(sf), setups))
    print(
        "Bag 3: Found %d setups with PC success greater than 0%%, outputting to output.txt"
        % len(pc_setups),
        end=' ')
    print("(Total elapsed time: %.2fsec)" %
          (time.perf_counter() - timer_start))

    with open("output.txt", "w+") as outputFile:
        for setup in sorted(
                pc_setups, key=(lambda s: s.PC_rate), reverse=True):
            outputFile.write(setup.tostring())
            outputFile.write("\n\n")


def main():
    findTSSTetrisPC()


if __name__ == '__main__':
    main()
