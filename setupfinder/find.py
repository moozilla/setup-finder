"""Command line entry point for setup-finder. Parse input.txt for setup to find, output results to output.html.

This will start as an extension to newjade's solution-finder and hopefully become a standalone utility.
Current sfinder version: solution-finder-0.511
"""

from pathlib import Path
import pickle
import time
import warnings
#from tqdm import tqdm, TqdmSynchronisationWarning
from setupfinder import output
from setupfinder.finder import finder


def parse_input_line(bag):
    """Parse a line from input.txt into a dict with default values.
    
    Arguments are separated by spaces, argument name and value separated by dash.
    Example line: TSD row-1,2 col-any filter-isTSD-any
    """
    bag_args = bag.split(' ')
    setup_type = bag_args.pop(0)
    # defaults
    bag_rows = []
    bag_cols = []
    bag_filter = None
    # todo: should be able to set height for overlays not just PCs, default should be 6 for non-PCs
    height = "4"
    pc_cutoff = 0.01
    for arg in bag_args:
        if arg[:3] == "col":
            if arg[4:] == "any":
                if setup_type == "TST":
                    bag_cols = [1, 2, 3, 4, 5, 6, 7, 8]
                elif setup_type == "Tetris":
                    bag_cols = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
                else:
                    # default for TSS, TSD
                    bag_cols = [1, 2, 3, 4, 5, 6, 7]
            else:
                bag_cols = list(map(int, arg[4:].split(',')))
        if arg[:3] == "row":
            bag_rows = list(map(int, arg[4:].split(',')))
        if arg[:6] == "filter":
            bag_filter = arg[7:]
        if arg[:6] == "height":
            height = arg[7:]
        if arg[:6] == "cutoff":
            pc_cutoff = float(arg[7:])
    return {
        'setup_type': setup_type,
        'rows': bag_rows,
        'cols': bag_cols,
        'filter': bag_filter,
        'height': height,
        'cutoff': pc_cutoff
    }


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

    pc_finish = False  # will determine how results are output
    with open(working_dir / "input.txt", "r") as input_file:
        bags = input_file.read().splitlines()

    setups = []
    title = ""  #title/heading of output.html
    pc_height = None  # these are used again in generating output
    pc_cutoff = None
    for i, bag in enumerate(bags):
        args = parse_input_line(bag)

        if args['setup_type'] == "PC":
            # note: this assumes there was a bag before PC finish, not intended to find pure PC setups
            print("Bag %d: Finding PCs..." % i)
            title += " -> PC"
            pc_height = args['height']
            pc_cutoff = args['cutoff']
            setups = finder.find_PC_setups(setups, pc_height, pc_cutoff,
                                           setup_cache)
            print("")  #newline so tqdm output isn't weird
            pc_finish = True
            break  # setup finding ends with a PC
        else:
            setup_func = finder.get_setup_func(
                args, find_mirrors=(i > 0), setup_cache=setup_cache)
            bag_title = args['setup_type'].split('-')[0]

        if i == 0:
            print("Bag %d: Finding %s initial bag setups..." % (i, bag_title))
            title = bag_title
            setups = finder.find_initial_setups(setup_func)
        else:
            print("Bag %d: Finding %s continuations..." % (i, bag_title))
            title += " -> " + bag_title
            setups = finder.find_continuations(setup_func, setups)
        #extra newline to make room for extra tqdm bar
        print("\nBag %d: Found %d valid setups" % (i, len(setups)))

    #with open(working_dir / "cache.bin", "wb") as cache_file:
    #    pickle.dump(setup_cache, cache_file, protocol=pickle.HIGHEST_PROTOCOL)
    print("Generating output file...")
    # image height is hardcoded for now (can I do something like determine max height at each step?)
    if pc_finish:
        output.output_results_pc(
            sorted(setups, key=(lambda s: s.PC_rate), reverse=True), title,
            pc_height, pc_cutoff, 7)
    else:
        output.output_results(
            sorted(setups, key=(lambda s: len(s.continuations)), reverse=True),
            title, 7, 4)
    print("Done.", end=' ')
    print(
        "(Total elapsed time: %.2fsec)" % (time.perf_counter() - timer_start))


def main():
    """Entry point for command-line."""
    working_dir = Path.cwd()
    #with warnings.catch_warnings():
    #warnings.simplefilter("ignore", TqdmSynchronisationWarning)
    setups_from_input(working_dir)
