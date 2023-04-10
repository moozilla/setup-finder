"""Generate output.html file for setup-finder results."""

from os import getcwd
from pathlib import Path
import warnings
from tqdm import tqdm, TqdmSynchronisationWarning
from dominate import document
from dominate.tags import h1, h2, div, p, img, a, b, pre
from dominate.util import text
from setupfinder.finder.sfinder import SFinder
from setupfinder.img import get_blocks_from_skin, fumen_to_image

working_dir = Path.cwd() / "output"
fumen_url = "http://104.236.152.73/fumen/?"  #"http://fumen.zui.jp/?"


def output_results_pc(output_file, setups, title, pc_height, pc_cutoff, img_height, cache, skin_file):
    skin = get_blocks_from_skin(skin_file)
    with open(output_file, "w+") as f:
        d = document(title=title)
        d += h1(title)
        d += p("%d setups found" % len(setups))
        with d:
            #annoying tqdm bug workaround
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", TqdmSynchronisationWarning)
                for i, setup in enumerate(tqdm(setups, unit="setup")):
                    generate_output_pc(setup, "Setup %d" % i, pc_cutoff, pc_height, img_height, skin, cache)
        f.write(d.render())


def output_results(output_file, setups, title, img_height, conts_to_display, skin_file):
    skin = get_blocks_from_skin(skin_file)
    with open(output_file, "w+") as f:
        d = document(title=title)
        d += h1(title)
        d += p("%d setups found" % len(setups))
        with d:
            #annoying tqdm bug workaround
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", TqdmSynchronisationWarning)
                for i, setup in enumerate(tqdm(setups, unit="setup")):
                    generate_output(setup, ("Setup %d" % i), img_height, conts_to_display, skin)
        f.write(d.render())


def generate_output(setup, title, img_height, conts_to_display, skin, imgs=[]):
    """Recursively generate output for setup+continuations."""
    #not the penultimate bag, need to go deeper
    if setup.continuations and len(setup.continuations[0].continuations) > 0:
        #store images in list to print at the end
        new_imgs = imgs.copy()  #don't think this needs to be a deepcopy
        new_imgs.append(fumen_to_image(setup.solution.fumen, img_height, skin))
        # this naming scheme could get messy, anything better? maybe Setup 1-A-A?
        # but I'm not sure what to do if more continuatons than 26, maybe just AA, then AAA
        new_ctd = conts_to_display - 1 if conts_to_display > 1 else 1
        for i, s in enumerate(tqdm(setup.continuations, unit="setup", leave=False)):
            generate_output(s, title + (" - Sub-Setup %d" % i), img_height, new_ctd, skin, new_imgs)
    else:
        h2(title)
        with div():
            for url in imgs:
                img(src=url)
            #final setup with conts, still need to display it's image
            img(src=fumen_to_image(setup.solution.fumen, img_height, skin))
            conts_to_display -= 1
            for cont in setup.continuations[:conts_to_display]:
                img(src=fumen_to_image(cont.solution.fumen, img_height, skin))
        with p():
            total_conts = len(setup.continuations)
            text("Showing ")
            b("%d" % min(conts_to_display, total_conts))
            text(" of ")
            b(a("%d continuations" % total_conts, href=fumen_url + setup.to_fumen()))


def generate_output_pc(setup, title, pc_cutoff, pc_height, img_height, skin, cache, imgs=[]):
    #not the penultimate bag, need to go deeper
    if setup.continuations and len(setup.continuations[0].continuations) > 0:
        #store images in list to print at the end
        new_imgs = imgs.copy()  #don't think this needs to be a deepcopy
        new_imgs.append(fumen_to_image(setup.solution.fumen, img_height, skin))
        for i, s in enumerate(tqdm(setup.continuations, unit="setup", leave=False)):
            generate_output_pc(s, title + (" - Sub-Setup %d" % i), pc_cutoff, pc_height, img_height, skin, cache,
                               new_imgs)
    else:
        sf = SFinder(setup_cache=cache)
        h2(title)
        with div():
            best_continuation = setup.continuations[0].solution
            best_pc = sf.path(
                fumen=best_continuation.to_fumen(), pieces=best_continuation.get_remaining_pieces(),
                height=pc_height)[0]  #todo: hack! change this when i fix cache

            for url in imgs:
                img(src=url)
            img(src=fumen_to_image(setup.solution.fumen, img_height, skin))
            img(src=fumen_to_image(best_continuation.fumen, img_height, skin))
            img(src=fumen_to_image(best_pc.fumen, img_height, skin))
        with p():
            text("Best continuation: ")
            b("%.2f%%" % setup.continuations[0].PC_rate)
            text(" PC success rate – ")
            b(a("%d continuations" % len(setup.continuations), href=fumen_url + setup.to_fumen()))
            text("with >%.2f%% PC success rate" % pc_cutoff)
