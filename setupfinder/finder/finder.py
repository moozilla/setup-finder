"""Find setups using lower-level modules.

The finder module is intended to be used by scripts to run any setup finding code.
Input and output should be done by the scripts themselves and then passed into and received from the finder module."""

from copy import deepcopy
from pathlib import Path
import gzip
import pickle
import colorama  # so tqdm looks good on windows
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
        solution.field.add_T(x - 1 if mirror else x + 1, y, True, mirror=not mirror)
        solution.sequence += "T"
        return solution.field.clearedRows == 3
    else:
        return False


def get_TSS_continuations(field, rows, cols, bag_filter, TSS1, TSS2, find_mirrors, use_cache=None):
    """Finds TSS continuations. Set TSS1 and TSS2 variables to choose which type.
    Find mirrors should be used to find setups with both left and right overhangs."""
    sf = SFinder(setup_cache=use_cache)
    solutions = []
    mirrors = [False, True] if find_mirrors else [False]
    # manual tqdm progress bar
    t = tqdm(total=len(rows) * len(cols) * (2 if TSS1 and TSS2 else 1) * len(mirrors), unit="setup", leave=False)
    for row in rows:
        for col in cols:
            for mirror in mirrors:
                # make copies to avoid mutating field
                if TSS1:
                    tss1_field = deepcopy(field)
                    # 6 is a reasonable height for blank field setups (7+ should be impossible in one bag)
                    # may want to have an option for different heights for finding tspins in other bags (prob pass an arg)
                    if tss1_field.add_overlay(gen.generate_TSS1(6, col, row, mirror)):
                        tss1_sols = sf.setup(fumen=gen.output_fumen(tss1_field.field))
                        # copy so we can try both flat and vertical T
                    else:
                        tss1_sols = []
                    t.update()
                    tss1_sols_copy = deepcopy(tss1_sols)
                if TSS2:
                    tss2_field = deepcopy(field)
                    if tss2_field.add_overlay(gen.generate_TSS2(6, col, row, mirror)):
                        tss2_sols = sf.setup(fumen=gen.output_fumen(tss2_field.field))

                    else:
                        tss2_sols = []
                    t.update()

                valid_sols = []
                if bag_filter == "isTSS-any":
                    # check if setup is actually a TSS (with all 7 pieces)
                    if TSS1:
                        valid_sols.extend(
                            filter(lambda sol: is_TSS(sol, col, row, vertical_T=False, mirror=mirror), tss1_sols))
                        valid_sols.extend(
                            filter(lambda sol: is_TSS(sol, col, row, vertical_T=True, mirror=mirror), tss1_sols_copy))
                    if TSS2:
                        valid_sols.extend(
                            filter(lambda sol: is_TSS(sol, col, row, vertical_T=False, mirror=mirror), tss2_sols))
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


def get_TSD_continuations(field, rows, cols, bag_filter, find_mirrors, use_cache=None):
    sf = SFinder(setup_cache=use_cache)
    solutions = []
    mirrors = [False, True] if find_mirrors else [False]
    # manual tqdm progress bar
    t = tqdm(total=len(rows) * len(cols) * len(mirrors), unit="setup", leave=False)
    for row in rows:
        for col in cols:
            for mirror in mirrors:
                # make copies to avoid mutating field
                tsd_field = deepcopy(field)
                if tsd_field.add_overlay(gen.generate_TSD(6, col, row, mirror)):
                    tsd_sols = sf.setup(fumen=gen.output_fumen(tsd_field.field))

                    valid_sols = []
                    if bag_filter == "isTSD-any":
                        valid_sols.extend(filter(lambda sol: is_TSD(sol, col, row), tsd_sols))
                    elif bag_filter == "testTSD":
                        valid_sols.extend(filter(lambda sol: test_TSD(sol, col, row), tsd_sols))
                    else:
                        valid_sols.extend(tsd_sols)
                    solutions.extend(valid_sols)
                t.update()
    t.close()
    return solutions


def get_TST_continuations(field, rows, cols, bag_filter, find_mirrors, use_cache=None):
    sf = SFinder(setup_cache=use_cache)
    solutions = []
    mirrors = [False, True] if find_mirrors else [False]
    # manual tqdm progress bar
    t = tqdm(total=len(rows) * len(cols) * len(mirrors), unit="setup", leave=False)
    for row in rows:
        for col in cols:
            for mirror in mirrors:
                # make copies to avoid mutating field
                tst_field = deepcopy(field)
                if tst_field.add_overlay(gen.generate_TST(6, col, row, mirror)):
                    tst_sols = sf.setup(fumen=gen.output_fumen(tst_field.field))

                    #sf.setup returns None if setup would require too many pieces
                    if tst_sols is not None:
                        valid_sols = []
                        if bag_filter == "isTST":
                            valid_sols.extend(filter(lambda sol: is_TST(sol, col, row, mirror), tst_sols))
                        else:
                            valid_sols.extend(tst_sols)
                        solutions.extend(valid_sols)
                t.update()
    t.close()
    return solutions


def get_Tetris_continuations(field, row, cols, use_cache=None):
    sf = SFinder(setup_cache=use_cache)
    solutions = []
    for col in cols:
        # make copies to avoid mutating field
        tet_field = deepcopy(field)
        # this height should be passed in (from input file?)
        tet_overlay = gen.generate_Tetris(7, col, row)
        if tet_field.add_overlay(tet_overlay):
            tet_sols = sf.setup(fumen=gen.output_fumen(tet_field.field, comment="-m o -f i -p *p7"))
            solutions.extend(tet_sols)
    return solutions


def get_setup_func(args, find_mirrors=False, setup_cache=None):
    """Return a function that can be applied to a field argument to find setups of the proper type.
    
    args is dict containing setup_type, rows, cols, filter, height, cutoff
    """
    if args['setup_type'] == "TSS-any" or args['setup_type'] == "TSS":
        return lambda field: get_TSS_continuations(field, args['rows'], args['cols'], args['filter'], True, True, find_mirrors, use_cache=setup_cache)
    elif args['setup_type'] == "TSS1":
        return lambda field: get_TSS_continuations(field, args['rows'], args['cols'], args['filter'], True, False, find_mirrors, use_cache=setup_cache)
    elif args['setup_type'] == "TSS2":
        return lambda field: get_TSS_continuations(field, args['rows'], args['cols'], args['filter'], False, True, find_mirrors, use_cache=setup_cache)
    elif args['setup_type'] == "TSD-any" or args['setup_type'] == "TSD":
        return lambda field: get_TSD_continuations(field, args['rows'], args['cols'], args['filter'], find_mirrors, use_cache=setup_cache)
    elif args['setup_type'] == "TST":
        return lambda field: get_TST_continuations(field, args['rows'], args['cols'], args['filter'], find_mirrors, use_cache=setup_cache)
    elif args['setup_type'] == "Tetris":
        # only supports 1 row for tetrises
        return lambda field: get_Tetris_continuations(field, args['rows'][0], args['cols'], use_cache=setup_cache)
    else:
        raise ValueError(f"Unknown setup type '{args['setup_type']}'.")


class Finder:
    def __init__(self, cache_file, pack_cache=False):
        self.setups = []
        self.pc_finish = False
        # these are used in generating PC paths in output, if "best_pc" is found here these could be removed
        self.pc_height = None
        self.pc_cutoff = None
        self.cache = {}  #initialize cache here
        self.cache_file = cache_file
        self.pack_cache = pack_cache  # if cache should be gzipped when saved

    def __enter__(self):
        """When used in a context-manager, load sfinder result cache from cache.bin."""
        if self.cache_file.exists():  # pylint: disable=E1101
            with open(self.cache_file, "rb") as f:
                # test magic bytes to see if cache is packed with gzip
                is_gzipped = f.read(2) == b'\x1f\x8b'
                # return to start of stream
                f.seek(0)
                if is_gzipped:
                    self.cache = pickle.load(gzip.GzipFile(fileobj=f))
                else:
                    self.cache = pickle.load(f)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.cache_file.exists():  # pylint: disable=E1101
            open_func = gzip.open if self.pack_cache else open
            with open_func(self.cache_file, "wb") as f:
                pickle.dump(self.cache, f, protocol=pickle.HIGHEST_PROTOCOL)
        return False  # don't supress any exceptions

    def find_initial_setups(self, args):
        """Initialize by finding blank-field setups specified by args."""
        setup_func = get_setup_func(args, find_mirrors=False, setup_cache=self.cache)
        # Apply setup function to blank field to get initial bag 'continuations.'
        self.setups = list(map(TetSetup, setup_func(TetField(from_list=[]))))

    def find_continuations(self, args):
        """Apply setup function (specified by args) to each setup to find it's continuations."""
        setup_func = get_setup_func(args, find_mirrors=True, setup_cache=self.cache)
        for setup in tqdm(self.setups, unit="setup"):
            setup.find_continuations(setup_func)
        # remove setups with no continuations
        self.setups = [setup for setup in self.setups if len(setup.continuations) > 0]

    def find_PC_finishes(self, args):
        """Find PC finishes for all setups."""
        # should check and make sure valid args are passed
        self.pc_height = args['height']
        self.pc_cutoff = args['cutoff']
        self.pc_finish = True
        self.setups = list(
            filter(lambda setup: setup.find_PCs(self.pc_height, self.pc_cutoff, use_cache=self.cache),
                   tqdm(self.setups, unit="setup")))
