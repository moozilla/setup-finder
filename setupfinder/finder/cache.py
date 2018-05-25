"""Save sfinder results for faster setup finding times."""

from os import getcwd
from os.path import isfile
from setupfinder.finder.tet import TetSolution, TetField
from setupfinder.finder import fumen
from pathlib import Path

#working_dir = "%s\\..\\%s" % (getcwd(), "cache")
working_dir = Path.cwd() / "cache"
backup_dir = Path.cwd() / "notes" / "old_cache"


def get_cache_file(fm):
    """Generate proper filename based on fumen."""
    # strip version str, strip ?, replace / with _ to make it safe for filenames
    # note: on windows filenames are case insensitive so collisions could occur, but this probably will never happen
    clean = fm.replace("v115@", "").replace("?", "").replace("/", "_").replace("*", "_")
    #return working_dir / (clean + ".txt")
    return clean + ".txt"


def get_solutions(fm):
    """Attempt to retrieve solutions from cache."""
    fname = get_cache_file(fm)
    cache_file = Path(working_dir / fname)
    if cache_file.exists():
        with cache_file.open() as f:
            sols = f.read().splitlines()
        # move to backup of old caches
        cache_file.rename(backup_dir / fname)
        solutions = []
        for sol in sols:
            field, seq = fumen.decode(sol)
            solutions.append(TetSolution(TetField(from_list=field), sol, seq))
        return solutions
    else:
        return None


'''def save_solutions(fm, solutions):
    """Save solutions in cache."""
    sols = "\n".join(map(lambda sol: sol.fumen, solutions))
    with open(get_cache_file(fm), "w+") as cacheFile:
        cacheFile.write(sols)


def save_PC_rate(fm, rate):
    """Save PC rate in cache."""
    with open(get_cache_file(fm), "w+") as cacheFile:
        cacheFile.write(rate)'''


def get_PC_rate(fm):
    """Attempt to retrieve PC rate from cache."""
    fname = get_cache_file(fm)
    cache_file = Path(working_dir / fname)
    if cache_file.exists():
        with cache_file.open() as f:
            rate = f.read()
        cache_file.rename(backup_dir / fname)
        return rate
    else:
        return None