"""Sfinder module, a wrapper for working with knewjade's solution-finder program."""

import re, subprocess
from lxml import html, etree
from os import getcwd
from tet import TetSetup

#solution finder version, used for finding default sfinder folder
SFINDER_VER = "solution-finder-0.511"


class SFinder:
    def __init__(self, working_dir=None):
        if working_dir is not None:
            self.working_dir = working_dir
        else:
            self.working_dir = "%s\\%s" % (getcwd(), SFINDER_VER)

    def setup(self, field=None, pieces=None, print_results=False, parent=None):
        """Run sfinder setup command, return setups"""
        args = ["java", "-Xmx1024m", "-jar", "sfinder.jar", "setup"]
        if field:
            args.extend(["-t", field])
        if pieces:
            args.extend(["-p", pieces])
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
                    fumens = []
                    fpieces = []
                    for child in section:
                        if child.tag == "p":
                            etree.strip_tags(child[0], "br")
                            field = child[0].text
                        if child.tag == "div":
                            fumens.append(child[0].attrib["href"].split(
                                "fumen.zui.jp/?")[1])
                            fpieces.append(child[0].text)
                    solutions.append(TetSetup(field, fumens, fpieces, parent))
                return solutions
            else:
                #only happens if it doesnt report 0 solutions - so never? maybe should raise exception
                print("Error: Setup didn't find any solutions\n\n" + output)
                return None
        except subprocess.CalledProcessError as e:
            print("Sfinder Error: %s" % re.search(r"Message: (.+)\n",
                                                  e.output).group(1))

    def percent(self, field=None, pieces=None, height=None):
        """Run sfinder percent command, return overall success rate (just the number)"""
        args = ["java", "-Xmx1024m", "-jar", "sfinder.jar", "percent"]
        if field:
            args.extend(["-t", field])
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
                return match.group(1)
            else:
                raise RuntimeError(
                    "Couldn't find percentage in sfinder output.\n\n" + output)
        except subprocess.CalledProcessError as e:
            print(e.output.splitlines()[2])

    def setInputTxt(self, field_diagram):
        """Set input.txt to a field diagram (string)."""
        with open(self.working_dir + "\\input\\field.txt", "w+") as f:
            f.write(field_diagram)