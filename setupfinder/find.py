"""Command line entry point for setup-finder. Parse input.txt for setup to find, output results to output.html.

This will start as an extension to newjade's solution-finder and hopefully become a standalone utility.
Current sfinder version: solution-finder-0.511
"""

from pathlib import Path
import pickle
import time
import warnings
from tqdm import tqdm, TqdmSynchronisationWarning
from setupfinder import output
from setupfinder.finder import finder


def setups_from_input(working_dir):
    # raise exception if input file not found? need a standard way of error handling for humans
    timer_start = time.perf_counter()
    print(working_dir)
    #with open(working_dir / "cache.bin", "rb") as cache_file:
    #setup_cache = pickle.load(cache_file)
    #rebuild cache if this fails
    #print("Time spent loading cache: %.2fsec" %
    #      (time.perf_counter() - timer_start))
    setup_cache = {}

    pc_height = None  # need to refactor this (all the arg stuff)
    pc_cutoff = None
    pc_finish = False  # will determine how results are output
    with open(working_dir / "input.txt", "r") as input_file:
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
                    if setup_type == "TST":
                        bag_cols = [1, 2, 3, 4, 5, 6, 7, 8]
                    elif setup_type == "Tetris":
                        bag_cols = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
                    else:
                        # default for TSS, TSD
                        bag_cols = [1, 2, 3, 4, 5, 6, 7, 7]
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

        if setup_type == "PC":
            print("Bag %d: Finding PCs..." % i)
            title += " -> PC"
            setups = list(
                filter(
                    lambda setup: setup.find_PCs(pc_height, pc_cutoff, use_cache=setup_cache),
                    tqdm(setups, unit="setup")))
            print("")  #newline so tqdm output isn't weird
            pc_finish = True
            break  # setup finding ends with a PC
        else:
            setup_func = finder.get_setup_func(setup_type, bag_rows, bag_cols,
                                               bag_filter, i > 0, setup_cache)
            bag_title = setup_type.split('-')[0]

        if i == 0:
            print("Bag %d: Finding %s initial bag setups..." % (i, bag_title))
            title = bag_title
            setups = finder.find_initial_setups(setup_func)
        else:
            print("Bag %d: Finding %s continuations..." % (i, bag_title))
            title += " -> " + bag_title
            for setup in tqdm(setups, unit="setup"):
                setup.find_continuations(setup_func)
            # remove setups with no continuations
            setups = [
                setup for setup in setups if len(setup.continuations) > 0
            ]
        #extra newline to make room for extra tqdm bar
        print("\nBag %d: Found %d valid setups" % (i, len(setups)))

    #with open(working_dir / "cache.bin", "wb") as cache_file:
    #    pickle.dump(setup_cache, cache_file, protocol=pickle.HIGHEST_PROTOCOL)
    print("Generating output file...")
    # image height is hardcoded for now (can I do something like determine max height at each step?)
    if pc_finish:
        output.output_results_pc(
            sorted(setups, key=(lambda s: s.PC_rate), reverse=True), title,
            pc_cutoff, pc_height, 7)
    else:
        output.output_results(
            sorted(setups, key=(lambda s: len(s.continuations)), reverse=True),
            title, 7, 4)
    print("Done.", end=' ')
    print(
        "(Total elapsed time: %.2fsec)" % (time.perf_counter() - timer_start))


def main():
    working_dir = Path.cwd()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", TqdmSynchronisationWarning)
        setups_from_input(working_dir)


if __name__ == '__main__':
    main()
