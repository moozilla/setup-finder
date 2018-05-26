"""Command line entry point for setup-finder. Parse input.txt for setup to find, output results to output.html.

This will start as an extension to newjade's solution-finder and hopefully become a standalone utility.
Current sfinder version: solution-finder-0.511
"""

from pathlib import Path
import time
import logging
#import warnings
#from tqdm import tqdm, TqdmSynchronisationWarning
from setupfinder import output
from setupfinder.finder import finder


def parse_input_line(bag):
    """Parse a line from input.txt into a dict with default values if args are missing.
    
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


def setups_from_input(input_file, cache_file, pack_cache):
    timer_start = time.perf_counter()

    #check if input file exists...
    with open(input_file, "r") as f:
        bags = f.read().splitlines()

    print("Initializing cache...")
    # using f in a with statement to initialize/output cache
    with finder.Finder(cache_file, pack_cache=False) as f:
        # should generate title from setup results
        title = ""  #title/heading of output.html
        for i, bag in enumerate(bags):
            args = parse_input_line(bag)
            bag_title = args['setup_type'].split('-')[0]

            if i == 0:
                print(f"Bag {i}: Finding {bag_title} initial bag setups...")
                title = bag_title
                f.find_initial_setups(args)
            else:
                if args['setup_type'] == "PC":
                    print(f"Bag {i}: Finding PCs...")
                    title += " -> PC"
                    f.find_PC_finishes(args)
                    break
                print(f"Bag {i}: Finding {bag_title} continuations...")
                title += " -> " + bag_title
                f.find_continuations(args)

            print(f"Bag {i}: Found {len(f.setups)} valid setups")

        print("Generating output file...")
        # image height is hardcoded for now (can I do something like determine max height at each step?)
        if f.pc_finish:
            output.output_results_pc(
                sorted(f.setups, key=(lambda s: s.PC_rate), reverse=True), title, f.pc_height, f.pc_cutoff, 7, f.cache)
        else:
            output.output_results(sorted(f.setups, key=(lambda s: len(s.continuations)), reverse=True), title, 7, 4)
        print("Saving cache...")
    print("Done.", end=' ')
    print(f"(Total elapsed time: {time.perf_counter() - timer_start:.2f}sec)")


def main():
    """Entry point for command-line."""
    #working_dir = Path.cwd()
    #with warnings.catch_warnings():
    #warnings.simplefilter("ignore", TqdmSynchronisationWarning)
    try:
        setups_from_input(Path("input.txt"), Path("cache.bin"), True)
    except Exception as e:
        if __debug__:
            raise
        logging.basicConfig(filename='error.log', level=logging.ERROR)
        logging.exception(e)
        print(f"Error: {e}")
        print(
            "See error.log for more details. Please consider opening an issue at: https://github.com/moozilla/setup-finder/issues"
        )
