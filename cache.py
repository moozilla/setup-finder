"""Save sfinder results for faster setup finding times."""

from os import getcwd
from os.path import isfile
from tet import TetSolution, TetField
import fumen

working_dir = "%s\\%s" % (getcwd(), "cache")


def get_cache_file(fm):
    """Generate proper filename based on fumen."""
    # strip version str, strip ?, replace / with _ to make it safe for filenames
    # note: on windows filenames are case insensitive so collisions could occur, but this probably will never happen
    clean = fm[5:].replace("?", "").replace("/", "_")
    return "%s\\%s.txt" % (working_dir, clean)


def get_solutions(fm):
    """Attempt to retrieve solutions from cache."""
    fname = get_cache_file(fm)
    if isfile(fname):
        with open(fname, "r") as cacheFile:
            sols = cacheFile.read().splitlines()
        solutions = []
        for sol in sols:
            field, seq = fumen.decode(sol)
            solutions.append(TetSolution(TetField(from_list=field), sol, seq))
        return solutions
    else:
        return None


def save_solutions(fm, solutions):
    """Save solutions in cache."""
    sols = "\n".join(map(lambda sol: sol.fumen, solutions))
    with open(get_cache_file(fm), "w+") as cacheFile:
        cacheFile.write(sols)