"""Find T-spin opener setups that end in a 3rd bag PC.

This will start as an extension to newjade's solution-finder and hopefully become a standalone utility.
Using: solution-finder-0.511
"""

import time
#from operator import itemgetter # for sorting
import sfinder, tet  # for code completion
from sfinder import SFinder
from tet import TetOverlay, TetSetupCollection


def isTSS(solution, verticalT=False):
    # for now, filter out solutions that use less than 6 pieces
    # (carrying over pieces into the next bag makes search space too large)

    # find # pieces by taking len of sequence str (all fumens should have same length)
    if len(solution.fumens[0][1]) == 6:
        # leaving each solution's field modfied is by design
        # this way it's as if sfinder had found solutions with Ts already placed
        solution.field.addT(2, 2, vertical=verticalT)
        solution.fumens = [(fs, seq + "T") for fs, seq in solution.fumens]
        return solution.field.clearedRows == 1
    else:
        return False


def findTSSTetrisPC():
    """Find setups that start with a TSS and end with a Tetris+PC."""
    sf = SFinder()
    print("Working dir: %s" % sf.working_dir)
    timer_start = time.perf_counter()

    print("Bag 1: Finding TSS setups...")
    bag1_sols = sf.setup(
        field="v115@pgQpBeXpBeXpBewhWpCeVpxhAe2hZpJeAgWPAtD98A?wG98AwzVTASokCA",
        pieces="[^T]!")
    print("Found %d solutions with possible TSS at 2,2" % len(bag1_sols))
    setups = TetSetupCollection(bag1_sols, isTSS)
    print("Bag 1: Found %d total valid TSS setups" % setups.length, end=' ')
    print("(Elapsed time: %.2fsec)" % (time.perf_counter() - timer_start))
    print("Bag 2: Adding overlays...")
    overlay = TetOverlay("""*........_
                            *........_
                            *........_
                            *********_
                            *********_
                            *********_
                            *********_""")
    setups.findContinuationsWithOverlay(overlay)
    print("Bag 2: Found %d valid continuation setups" % setups.length, end=' ')
    print("(Elapsed time: %.2fsec)" % (time.perf_counter() - timer_start))
    '''bag2_continuations = list(
        filter(lambda setup: setup.addOverlay(overlay), bag1_setups))
    print("Bag 2: Found %d possible continuations with overlay" %
          len(bag2_continuations))
    bag2_setups = []
    for cont in bag2_continuations:
        cont.outputInputTxt(sf)  #output diagram to sfinder's input.txt
        #run without args to use input.txt and *p7 piece seq
        setups = sf.setup(parent=cont)
        if setups is not None and len(setups) > 0:
            bag2_setups.extend(setups)


    print("Bag 3: Finding PCs...")
    bag3_pcs = 0
    with open("output.txt", "w+") as outputFile:
        for setup in bag2_setups:
            setup.findPCs(sf, "7")
            if setup.PC_rate > 0.00:
                bag3_pcs += 1
                outputFile.write(setup.tostring())
                outputFile.write("\n\n")
    print(
        "Bag 3: Found %d PCs with success greater than 0%%, outputting to output.txt"
        % bag3_pcs,
        end=' ')
    print("(Total elapsed time: %.2fsec)" %
          (time.perf_counter() - timer_start)) '''


def main():
    findTSSTetrisPC()


if __name__ == '__main__':
    main()
