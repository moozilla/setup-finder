"""Generate output.html file for setup-finder results."""

from os import getcwd
from dominate import document
from dominate.tags import h1, h2, div, p, img, a, b, pre
from dominate.util import text
from sfinder import SFinder
from tqdm import tqdm, TqdmSynchronisationWarning
import warnings

working_dir = "%s\\%s" % (getcwd(), "output")


def output_results(setups, title, pc_cutoff, pc_height, img_height):
    sf = SFinder()
    with open("%s\\output.html" % working_dir, "w+") as output_file:
        d = document(title=title)
        d += h1(title)
        d += p("%d setups found" % len(setups))
        with d:
            #annoying tqdm bug workaround
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", TqdmSynchronisationWarning)
                for i, setup in enumerate(tqdm(setups, unit="setup")):
                    h2("Setup %d" % i)
                    with div():
                        best_continuation = setup.continuations[0].solution
                        best_pc = sf.path(
                            fumen=best_continuation.to_fumen(),
                            pieces=best_continuation.get_remaining_pieces(),
                            height=pc_height,
                            use_cache=True)[0]

                        img(src=sf.fig_png(setup.solution.fumen, img_height))
                        img(
                            src=sf.fig_png(best_continuation.fumen,
                                           img_height))
                        img(src=sf.fig_png(best_pc.fumen, img_height))
                    with p():
                        text("Best continuation: ")
                        b("%.2f%%" % setup.continuations[0].PC_rate)
                        text(" PC success rate – ")
                        b(
                            a("%d continuations" % len(setup.continuations),
                              href="http://fumen.zui.jp/?%s" %
                              setup.to_fumen()))
                        text("with >%.2f%% PC success rate" % pc_cutoff)
        output_file.write(d.render())
