"""Sfinder module, a wrapper for working with knewjade's solution-finder program."""

import os, re, subprocess, tet
from lxml import html, etree
from tet import TetSolution, TetField
import cache
from fumen import decode

#solution finder version, used for finding default sfinder folder
SFINDER_VER = "solution-finder-0.511"


class SFinder:
    def __init__(self, working_dir=None):
        if working_dir is not None:
            self.working_dir = working_dir
        else:
            self.working_dir = "%s\\%s" % (os.getcwd(), SFINDER_VER)

    def setup(self,
              fumen=None,
              pieces=None,
              input_diagram=None,
              print_results=False,
              use_cache=False):
        """Run sfinder setup command, return setups.
        
        Returns a list of TetSolutions.
        """
        if use_cache == True and fumen is not None:
            cached_result = cache.get_solutions(fumen)
            if cached_result is not None:
                return cached_result
        args = ["java", "-Xmx1024m", "-jar", "sfinder.jar", "setup"]
        if fumen:
            args.extend(["-t", fumen])
        if pieces:
            args.extend(["-p", pieces])
        if input_diagram:
            self.setInputTxt(input_diagram)
        try:
            output = subprocess.check_output(
                args,
                cwd=self.working_dir,
                stderr=subprocess.STDOUT,
                universal_newlines=True)
            match = re.search(r"Found solution = (\d+)\D+time = (\d+)", output)
            if match:
                if print_results:
                    print("Setup found %s solutions, took %s ms\n" %
                          match.group(1, 2))
                #parse setup.html for solutions
                with open(self.working_dir + "\\output\\setup.html", "r") as f:
                    setupHtml = f.read()
                tree = html.fromstring(setupHtml)
                sections = tree.xpath("//section")
                solutions = []
                for section in sections:
                    for child in section:
                        if child.tag == "p":
                            etree.strip_tags(child[0], "br")
                            field_str = child[0].text
                        if child.tag == "div":
                            solutions.append(
                                TetSolution(
                                    TetField(from_string=field_str),
                                    child[0].attrib["href"].split(
                                        "fumen.zui.jp/?")[1],
                                    child[0].text))
                if use_cache:
                    cache.save_solutions(fumen, solutions)
                return solutions
            else:
                #only happens if it doesnt report 0 solutions - so never? maybe should raise exception
                print("Error: Setup didn't find any solutions\n\n" + output)
                return None
        except subprocess.CalledProcessError as e:
            raise RuntimeError("Sfinder Error: %s" % re.search(
                r"Message: (.+)\n", e.output).group(1))

    def path(self, fumen=None, pieces=None, height=None, use_cache=False):
        """Run sfinder path command, returns a list of solution fumens.
        
        Note: Doesn't parse sequences possible for each fumen, could add this later. (Might want to change to parsing csv for that?)"""
        if use_cache == True and fumen is not None:
            cached_result = cache.get_solutions(fumen)
            if cached_result is not None:
                return cached_result
        args = ["java", "-Xmx1024m", "-jar", "sfinder.jar", "path"]
        if fumen:
            args.extend(["-t", fumen])
        if pieces:
            args.extend(["-p", pieces])
        if height:
            args.extend(["-c", height])
        try:
            output = subprocess.check_output(
                args,
                cwd=self.working_dir,
                stderr=subprocess.STDOUT,
                universal_newlines=True)
            match = re.search(r"Found path \[minimal\] = (\d+)", output)
            if match:
                # maybe should have an option for which path result it uses? but going with minimal for now
                with open(
                        self.working_dir + "\\output\\path_minimal.html",
                        "r",
                        encoding="utf-8") as f:
                    setupHtml = f.read()
                tree = html.fromstring(setupHtml)
                divs = tree.xpath("//section//div")
                solutions = []
                for div in divs:
                    fumen_str = div[0].attrib["href"].split("fumen.zui.jp/?")[
                        1]
                    field, seq = decode(fumen_str)
                    # actually kind of silly saving field at all considering it's just cleared lines, but whatever
                    solutions.append(
                        TetSolution(TetField(from_list=field), fumen_str, seq))
                if use_cache:
                    cache.save_solutions(fumen, solutions)
                return solutions
            else:
                #only happens if it doesnt report 0 solutions - so never? maybe should raise exception
                print("Error: Path didn't find any solutions\n\n" + output)
                return None
        except subprocess.CalledProcessError as e:
            raise RuntimeError("Sfinder Error: %s" % re.search(
                r"Message: (.+)\n", e.output).group(1))

    def percent(self, fumen=None, pieces=None, height=None, use_cache=False):
        """Run sfinder percent command, return overall success rate (just the number)"""
        if use_cache == True and fumen is not None and pieces is not None:
            # "r" for rate, I'll use "p" if I implement path later on
            cached_result = cache.get_PC_rate("r" + pieces + fumen)
            if cached_result is not None:
                return cached_result
        args = ["java", "-Xmx1024m", "-jar", "sfinder.jar", "percent"]
        if fumen:
            args.extend(["-t", fumen])
        if pieces:
            args.extend(["-p", pieces])
        if height:
            args.extend(["-c", height])
        try:
            output = subprocess.check_output(
                args,
                cwd=self.working_dir,
                stderr=subprocess.STDOUT,
                universal_newlines=True)
            match = re.search(r"success = (\d+\.\d+)%", output)
            if match:
                pc_rate = match.group(1)
                if use_cache:
                    cache.save_PC_rate("r" + pieces + fumen, pc_rate)
                return pc_rate
            else:
                raise RuntimeError(
                    "Couldn't find percentage in sfinder output.\n\n" + output)
        except subprocess.CalledProcessError as e:
            raise RuntimeError("Sfinder Error: %s" % re.search(
                r"Message: (.+)\n", e.output).group(1))

    def fig_png(self, fumen, dest, height):
        """Generate an image for a fumen using 'util fig' then move it to destination."""
        args = ["java", "-jar", "sfinder.jar", "util", "fig"]
        args.extend(["-t", fumen])
        # output to png, no hold/next, end after 1st frame (to only make 1 image)
        args.extend(["-F", "png", "-f", "no", "-e", "1"])
        args.extend(["-l", height])
        try:
            output = subprocess.check_output(
                args,
                cwd=self.working_dir,
                stderr=subprocess.STDOUT,
                universal_newlines=True)
            match = re.search(r"\.\.\.\. Output to (.+\\\d+_\d+)", output)
            if match:
                img_dir = match.group(1)
                #remove file if it exists
                try:
                    os.remove(dest)
                except FileNotFoundError:
                    pass
                os.rename(img_dir + "\\fig_001.png", dest)
                #note: will fail if dir isn't empty, which is should always be after file is moved
                os.rmdir(img_dir)
            else:
                raise RuntimeError(
                    "Couldn't find image path in sfinder output.\n\n" + output)
        except subprocess.CalledProcessError as e:
            raise RuntimeError("Sfinder Error: %s" % re.search(
                r"Message: (.+)\n", e.output).group(1))

    def setInputTxt(self, field_diagram):
        """Set input.txt to a field diagram (string)."""
        with open(self.working_dir + "\\input\\field.txt", "w+") as f:
            f.write(field_diagram)