"""Find T-spin opener setups that end in a 3rd bag PC.

This will start as an extension to newjade's solution-finder and hopefully become a standalone utility.
Using: solution-finder-0.511
"""

import time
#from operator import itemgetter # for sorting
from sfinder import SFinder
from tet import TetOverlay


def findTSSTetrisPC():
    """Find setups that start with a TSS and end with a Tetris+PC."""
    sf = SFinder()
    print("Working dir: %s" % sf.working_dir)
    timer_start = time.perf_counter()

    bag1_setups = []
    print("Bag 1: Finding TSS setups...")
    tss_2_2 = sf.setup(
        field="v115@pgQpBeXpBeXpBewhWpCeVpxhAe2hZpJeAgWPAtD98A?wG98AwzVTASokCA",
        pieces="[^T]!")
    print("Found %d setups with TSS at 2,2" % len(tss_2_2))
    for setup in tss_2_2:
        # for now, ignore setups that don't use a full bag
        if len(setup.fumens[0].pieces) == 6:
            setup.field.addT(2, 2, vertical=True)
            if setup.field.clearedRows == 1:
                # only add if actually a TSS (this avoids TSD solutions)
                bag1_setups.append(setup)
    print("Bag 1: Found %d total valid TSS setups" % len(bag1_setups), end=' ')
    print("(Elapsed time: %.2fsec)" % (time.perf_counter() - timer_start))

    print("Bag 2: Adding overlays...")
    overlay = TetOverlay("""*........_
                            *........_
                            *........_
                            *********_
                            *********_
                            *********_
                            *********_""")
    bag2_continuations = list(
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
    print(
        "Bag 2: Found %d valid continuation setups" % len(bag2_setups),
        end=' ')
    print("(Elapsed time: %.2fsec)" % (time.perf_counter() - timer_start))

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
          (time.perf_counter() - timer_start))


def main():
    findTSSTetrisPC()


if __name__ == '__main__':
    main()
