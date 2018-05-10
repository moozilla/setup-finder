"""Generate output.html file for setup-finder results."""

from os import getcwd
from dominate import document
from dominate.tags import h1, h2, div, p, img, a, b, pre
from dominate.util import text
from sfinder import SFinder
from tqdm import tqdm, TqdmSynchronisationWarning
import warnings

working_dir = "%s\\%s" % (getcwd(), "output")


def output_results(setups, title, cutoff):
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
                        pc_height = "7"  # need to get img height programmatically somewhere
                        best_continuation = setup.continuations[0].solution
                        best_pc = sf.path(
                            fumen=best_continuation.fumen,
                            pieces=best_continuation.get_remaining_pieces(),
                            height=pc_height,
                            use_cache=True)[0]

                        img_dest = "%s\\setup%d_fig1.png" % (working_dir, i)
                        sf.fig_png(setup.solution.fumen, img_dest, pc_height)
                        img(src=img_dest)

                        img_dest = "%s\\setup%d_fig2.png" % (working_dir, i)
                        sf.fig_png(best_continuation.fumen, img_dest,
                                   pc_height)
                        img(src=img_dest)

                        img_dest = "%s\\setup%d_fig3.png" % (working_dir, i)
                        sf.fig_png(best_pc.fumen, img_dest, pc_height)
                        img(src=img_dest)
                    with p():
                        text("Best continuation: ")
                        b("%.2f%%" % setup.continuations[0].PC_rate)
                        text(" PC success rate – ")
                        b(
                            a("%d continuations" % len(setup.continuations),
                              href="http://fumen.zui.jp/?%s" %
                              setup.to_fumen()))
                        text("with >%.2f%% PC success rate" % cutoff)
        output_file.write(d.render())
