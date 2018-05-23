"""
'tet' module, contains a bunch of classes used for dealing with Tetris fields, fumen diagrams, and opener specifications

From simple->complex:
* TetField - representation of Tetris matrix, methods for importing/exporting diagram representations, and manipulations
* TetOverlay - equivalent of TetField, for overlaying on top of TetFields (class exists so later it can be used to generate overlays for Tspins, etc)
* TetSolution - basic sfinder results, setup.html is parsed for these
* TetSetup - TetSolution + continuations (either further TetSetup bags/steps or PCs)
"""

from setupfinder.finder import sfinder, fumen
from tqdm import tqdm


class TetField:
    """Simple implementation of Tetris matrix, no colors, just filled and empty blocks."""

    def __init__(self, from_string=None, from_list=None):
        """Generates matrix from field diagram.
        
        Note that in input, rows are NOT separated by newlines (html processing strips <br> elements).
        """
        self.clearedRows = 0  # keep track of cleared rows to figure out PC height
        if from_string is not None:
            self.height = len(from_string) // 10
            self.field = []
            i = 0
            for _ in range(self.height):
                row = [0] * 10
                for x in range(10):
                    row[x] = 1 if (from_string[i] == "X") else 0
                    i += 1
                # insert row at top, because diagram is top->bottom but field bottom is y=0
                self.field.insert(0, row)
        if from_list is not None:
            self.field = [[1 if b > 0 else 0 for b in row]
                          for row in from_list]  # colors -> 1s and 0s
            self.height = len(self.field)

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

    def add_T(self, x, y, vertical=False, mirror=False):
        """Add a T piece to the field (x,y) marks center of piece. For now vertical Ts point right"""
        if vertical:
            #todo: fix this, this is really hacky
            if mirror:
                self.field[y + 1][x] = 1
                self.field[y][x] = 1
                self.field[y][x - 1] = 1
                self.field[y - 1][x] = 1
            else:
                self.field[y + 1][x] = 1
                self.field[y][x] = 1
                self.field[y][x + 1] = 1
                self.field[y - 1][x] = 1
        else:
            self.field[y][x - 1] = 1
            self.field[y][x] = 1
            self.field[y][x + 1] = 1
            self.field[y - 1][x] = 1
        self.clear_rows()

    def clear_rows(self):
        self.field = [row for row in self.field if row != ([1] * 10)]
        newHeight = len(self.field)
        self.clearedRows += self.height - newHeight
        # print("Cleared %d rows" % (self.height - newHeight))
        self.height = newHeight

    def add_overlay(self, overlay):
        """
        Add overlay onto field for generating further setups.
        2 = fill, 3 = margin, 0 = must be blank
        Returns True if successful (only fails if must be blank cell isn't blank)"""
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


class TetOverlay:
    """Overlay wrapper, for importing/generating overlays.
    
    Overlays are basically what I am calling a setup diagram that is superimposed onto the current setup.
    Eventually, this class will have functions to generate overlays to find Tspins, etc., on top of an arbitrary field
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


class TetSolution:
    """Wrapper for sfinder solutions. Setups with multiple fumens are split into multiple TetSolutions for simplicity."""

    def __init__(self, field, fumen, sequence):
        self.field = field
        self.fumen = fumen
        self.sequence = sequence
        #self.PC_rate = None

    #honestly have no idea which class this shoud be in
    def add_overlay(self, tetOverlay):
        return self.field.add_overlay(tetOverlay.overlay)

    def get_remaining_pieces(self):
        """Takes a piece sequence and returns an sfinder piece selector containing the missing pieces + *p7"""
        nextPieces = "*p7"
        remaining = ','.join([p for p in "LJSZIOT" if p not in self.sequence])
        if remaining:
            nextPieces = remaining + "," + nextPieces
        return nextPieces

    def tostring(self):
        ret = self.field.tostring()
        ret += "\n\nFumen: %s\n" % self.fumen
        #if self.PC_rate is not None:
        #    ret += " (%s%%)" % self.PC_rate
        return ret

    def to_fumen(self):
        """Return a fumen with current field/seq (since field will be modified during T-spins, etc.)."""
        fixed_colors = [[[0, 8, 1, 3][b] for b in row]
                        for row in self.field.field]
        return fumen.encode([(fixed_colors, self.sequence)])


class TetSetup:
    """Collection of solutions filtered to fit a certain specification."""

    def __init__(self, solution):
        self.solution = solution
        self.continuations = []
        self.PC_rate = 0.00
        #self.depth?

    def get_fumen(self, comment):
        """Encode setup's field as a fumen diagram for inputting to sfinder."""
        fixed_colors = [[[0, 8, 1, 3][b] for b in row]
                        for row in self.solution.field.field]
        return fumen.encode([(fixed_colors, comment)])

    def add_continuations(self, setups):
        #print("Adding %d continations" % len(setups))
        if setups is not None and len(setups) > 0:
            #map is because this is passed TetSolutions (need to fix this?)
            self.continuations.extend(map(TetSetup, setups))
            return True
        else:
            return False

    def find_continuations(self, setup_func):
        """Recursively find and add continuations with function passed as setup_func."""
        if len(self.continuations) > 0:
            for cont in tqdm(self.continuations, unit="continuation"):
                cont.find_continuations(setup_func)
            # remove setups with no continuations
            self.continuations = [
                setup for setup in self.continuations
                if len(setup.continuations) > 0
            ]
        else:
            new_conts = setup_func(self.solution.field)
            self.add_continuations(new_conts)

    def find_PCs(self, height, cutoff, use_cache):
        """Find PCs for all continuations, then figure out overall PC rate.
        
        Returns true if overall PC rate is >= cutoff, for filtering.
        """
        if len(self.continuations) > 0:
            # find PCs for all continuations, filter out continuations without PCs
            try:
                self.continuations = list(
                    filter(
                        lambda cont: cont.find_PCs(height, cutoff, use_cache),
                        tqdm(self.continuations, unit="PC")))
            except:
                print("Parent of problem cont: " + self.solution.tostring())
                raise
            if len(self.continuations) == 0:
                # no PCs found
                self.PC_rate = 0.00
                return False
            # sort continuations by PC rate (descending)
            self.continuations = sorted(
                self.continuations,
                key=(lambda cont: cont.PC_rate),
                reverse=True)
            self.PC_rate = max([cont.PC_rate for cont in self.continuations])
            # if best PC is 100%, count number of 100%s for sorting (make sure to adjust for this if it is ever displayed)
            if self.PC_rate == 100.00:
                self.PC_rate += [cont.PC_rate for cont in self.continuations
                                 ].count(100.00) - 1
        else:
            # note: changing solution.fumen to solution.to_fumen() might invalidate old cache results
            try:
                if self.solution.field.height > int(height):
                    # stack too high for desired PC, don't even try
                    self.PC_rate = 0.00
                else:
                    #with sfinder.SFinder() as sf:
                    sf = sfinder.SFinder()
                    self.PC_rate = float(
                        sf.percent(
                            self.solution.to_fumen(),
                            self.solution.get_remaining_pieces(),
                            height,
                            use_cache=use_cache))
            except:
                print("Problem cont: " + self.solution.tostring())
                raise
        return self.PC_rate >= cutoff

    def tostring(self, cont=False):
        """Pretty print for outputing to results txt file."""
        ret = self.solution.tostring()
        if len(self.continuations) > 0:
            ret += "Continuations:\n"
            for cont in self.continuations:
                # todo: i think i need to recurse all the way down for 4bag PCs, also don't display % for non-PC results
                ret += "%s (%.2f%%)\n" % (cont.solution.fumen, cont.PC_rate)
        return ret

    def to_fumen(self):
        """Output setup + continuations in one fumen."""
        if len(self.continuations) > 0:
            frames = [fumen.decode(self.solution.fumen)]
            for cont in self.continuations:
                field, _ = fumen.decode(cont.solution.fumen)
                comment = "%.2f%%" % cont.PC_rate if cont.PC_rate > 0 else ""
                frames.append((field, comment))
            #print(frames)
            return fumen.encode(frames)
        else:
            return self.solution.fumen