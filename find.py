"""Find T-spin opener setups that end in a 3rd bag PC.

This will start as an extension to newjade's solution-finder and hopefully become a standalone utility.
Using: solution-finder-0.511
"""

import re, subprocess, time
from subprocess import check_output
from lxml import html, etree
from operator import itemgetter

sfinderPath = "C:/Users/metazilla/code/setup-finder/solution-finder-0.511"


class TetField:
    """Simple implementation of Tetris matrix, no colors, just filled and empty blocks."""

    def __init__(self, fromstring):
        self.height = len(fromstring) // 10
        self.clearedRows = 0  # keep track of cleared rows to figure out PC height
        self.field = []
        i = 0
        for _ in range(self.height):
            row = [0] * 10
            for x in range(10):
                row[x] = 1 if (fromstring[i] == "X") else 0
                i += 1
            # insert row at top, because diagram is top->bottom but field bottom is y=0
            self.field.insert(0, row)

    def tostring(self):
        rows = []
        for y in range(self.height):
            row = ""
            for x in range(10):
                row += "_X*." [self.field[y][
                    x]]  #"X" if (self.field[y][x] == 1) else "_"
            rows.insert(0, row)
            #str = row + "\n" + str  # display field top->bottom
        return "\n".join(rows)

    def addT(self, x, y, vertical=False):
        """Add a T piece to the field (x,y) marks center of piece. For now vertical Ts point right"""
        if vertical:
            self.field[y + 1][x] = 1
            self.field[y][x] = 1
            self.field[y][x + 1] = 1
            self.field[y - 1][x] = 1
        else:
            self.field[y][x - 1] = 1
            self.field[y][x] = 1
            self.field[y][x + 1] = 1
            self.field[y - 1][x] = 1
        self.clearRows()

    def clearRows(self):
        self.field = [row for row in self.field if row != ([1] * 10)]
        newHeight = len(self.field)
        self.clearedRows += self.height - newHeight
        # print("Cleared %d rows" % (self.height - newHeight))
        self.height = newHeight

    def addOverlay(self, overlay):
        """
        Add overlay onto field for generating further setups.
        2 = fill, 3 = margin, 0 = no change
        Only overwrites cells that are 0 (not already filled)."""
        newHeight = len(overlay)
        if newHeight > self.height:  #add blank rows if necessary
            self.field.extend([[0] * 10 for _ in range(newHeight)])
            self.height = newHeight
        for y in range(self.height):
            for x in range(10):
                if self.field[y][x] == 0:
                    self.field[y][x] = overlay[y][x]
                else:
                    #should be hole, but is filled
                    if overlay[y][x] == 0: return False
        return True


class TetSetup:
    """Field + fumen diagrams for each step"""

    def __init__(self, fieldstr, fumens, pieces, parent=None):
        self.field = TetField(fieldstr)
        self.fumens = []
        for fumen, pieceSeq in zip(fumens, pieces):
            self.fumens.append(TetFumen(fumen, pieceSeq))
        self.parent = parent  #previous setup
        self.PC_rate = 0.00

    def __repr__(self):
        return self.tostring()

    def tostring(self):
        if self.parent:
            ret = "\n".join([
                "  ".join(a)
                for a in zip(self.parent.field.tostring().split("\n"),
                             self.field.tostring().split("\n"))
            ])
        else:
            ret = self.field.tostring()
        ret += "\n\n"
        #flist = []
        #plist = []
        #for fumen in self.fumens:
        #    flist.append(fumen.fumen)
        #    plist.append(fumen.pieces)
        if self.parent:
            ret += "Parent Fumen: %s\n" % ", ".join(
                [fm.tostring() for fm in self.parent.fumens])  # pylint: disable=E1101
        ret += "Fumen: %s\n" % ", ".join([fm.tostring() for fm in self.fumens])  # pylint: disable=E1101
        if self.PC_rate > 0.00:
            ret += "Best PC Rate: %.2f" % self.PC_rate
        #ret += "\nSequence: %s\n" % ", ".join(plist)
        return ret

    def addOverlay(self, tetOverlay):
        return self.field.addOverlay(tetOverlay.overlay)

    def outputInputTxt(self):
        with open(sfinderPath + "/input/field.txt", "w") as f:
            f.write(self.field.tostring())

    def findPCs(self, height):
        for fumen in self.fumens:
            fumen.findPC(height)
            pcr = float(fumen.PC_rate)
            if pcr > self.PC_rate:
                self.PC_rate = pcr


class TetFumen:
    """Wrapper for fumen + piece sequence"""

    def __init__(self, fumen, pieces):
        self.fumen = fumen
        self.pieces = pieces
        self.PC_rate = None

    def findPC(self, height):
        """Find PC percent rate. (height and result are strings)"""
        self.PC_rate = sfinderPercent(
            field=self.fumen,
            pieces=getRemainingPieces(self.pieces),
            height=height)

    def tostring(self):
        ret = self.fumen
        if self.PC_rate is not None:
            ret += " (%s%%)" % self.PC_rate
        return ret


class TetOverlay:
    """Overlay wrapper, for importing/generating overlays.
    
    Overlays are basically what I am calling a setup diagram that is superimposed onto the current setup.
    """

    def __init__(self, overlayString):
        """Import from string, rows split by newlines, same format as sfinder diagrams."""
        #can have tabs/spaces as indents, splits by whitespace
        diagramRows = overlayString.split()
        diagramRows.reverse()
        self.height = len(diagramRows)
        self.overlay = [
            list(map(lambda c: '_X*.'.index(c), row)) for row in diagramRows
        ]


def sfinderSetup(field=None, pieces=None, printResults=False, parent=None):
    """Run sfinder setup command, return setups"""
    args = ["java", "-Xmx1024m", "-jar", "sfinder.jar", "setup"]
    if field:
        args.extend(["-t", field])
    if pieces:
        args.extend(["-p", pieces])
    try:
        output = check_output(
            args,
            cwd=sfinderPath,
            stderr=subprocess.STDOUT,
            universal_newlines=True)
        match = re.search(r"Found solution = (\d+)\D+time = (\d+)", output)
        if match:
            if printResults:
                print("Setup found %s solutions, took %s ms\n" % match.group(
                    1, 2))
            #parse setup.html for solutions
            with open(sfinderPath + "/output/setup.html", "r") as f:
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
                        fumens.append(
                            child[0].attrib["href"].split("fumen.zui.jp/?")[1])
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


def sfinderPercent(field=None, pieces=None, height=None):
    """Run sfinder percent command, return overall success rate (just the number)"""
    args = ["java", "-Xmx1024m", "-jar", "sfinder.jar", "percent"]
    if field:
        args.extend(["-t", field])
    if pieces:
        args.extend(["-p", pieces])
    if height:
        args.extend(["-c", height])
    try:
        output = check_output(
            args,
            cwd=sfinderPath,
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


def getRemainingPieces(pieces):
    """Takes a piece sequence and returns an sfinder piece selector containing the missing pieces + *p7"""
    nextPieces = "*p7"
    remaining = ','.join(set("LJSZIOT") - set(pieces))
    if remaining:
        nextPieces = remaining + "," + nextPieces
    return nextPieces


def findTSSTetrisPC():
    """Find setups that start with a TSS and end with a Tetris+PC."""
    timer_start = time.perf_counter()

    # Bag 1
    bag1_setups = []

    #todo: currently this also finds TSDs
    print("Bag 1: Finding TSS setups...")
    tss_2_2 = sfinderSetup(
        field="v115@pgQpBeXpBeXpBewhWpCeVpxhAe2hZpJeAgWPAtD98A?wG98AwzVTASokCA",
        pieces="[^T]!")
    print("Found %d setups with TSS at 2,2" % len(tss_2_2))
    for setup in tss_2_2:
        # for now, ignore setups that don't use a full bag
        if len(setup.fumens[0].pieces) == 6:
            setup.field.addT(2, 2, vertical=True)
            if setup.field.clearedRows == 1:
                # only add if actually a TSS (this avoids TSD solutions)
                bag1_setups.append(setup)
    '''     tss_3_2 = sfinderSetup(
        field="v115@pgSpBeXpBeWpwhBeWpCeUpyhAe1hZpJeAgWPAtD98A?wG98AwzVTASokCA",
        pieces="[^T]!")
    print("Found %d setups with TSS at 3,2" % len(tss_3_2))
    for setup in tss_3_2:
        if len(setup.fumens[0].pieces) == 6:
            setup.field.addT(3, 2, vertical=True)
            if setup.field.clearedRows == 1:
                bag1_setups.append(setup) '''

    print("Bag 1: Found %d total valid TSS setups" % len(bag1_setups), end=' ')
    print("(Elapsed time: %.2fsec)" % (time.perf_counter() - timer_start))

    print("Bag 2: Adding overlays...")
    overlay = TetOverlay("""*........_
                            *........_
                            *........_
                            *********_
                            *********_
                            *********_
                            *********_""")
    bag2_continuations = list(
        filter(lambda setup: setup.addOverlay(overlay), bag1_setups))
    print("Bag 2: Found %d possible continuations with overlay" %
          len(bag2_continuations))
    bag2_setups = []
    for cont in bag2_continuations:
        cont.outputInputTxt()  #output diagram to sfinder's input.txt
        #run without args to use input.txt and *p7 piece seq
        setups = sfinderSetup(parent=cont)
        if setups is not None and len(setups) > 0:
            bag2_setups.extend(setups)
    print(
        "Bag 2: Found %d valid continuation setups" % len(bag2_setups),
        end=' ')
    print("(Elapsed time: %.2fsec)" % (time.perf_counter() - timer_start))

    print("Bag 3: Finding PCs...")
    bag3_pcs = 0
    with open("output.txt", "w+") as outputFile:
        for setup in bag2_setups:
            setup.findPCs("7")
            if setup.PC_rate > 0.00:
                bag3_pcs += 1
                outputFile.write(setup.tostring())
                outputFile.write("\n\n")
    print(
        "Bag 3: Found %d PCs with success greater than 0%%, outputting to output.txt"
        % bag3_pcs,
        end=' ')
    print("(Total elapsed time: %.2fsec)" %
          (time.perf_counter() - timer_start))


def main():
    findTSSTetrisPC()


if __name__ == '__main__':
    main()
