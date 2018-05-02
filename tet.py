"""
'tet' module, contains a bunch of classes used for dealing with Tetris fields, fumen diagrams, and opener specifications

From simple->complex:
* TetField - representation of Tetris matrix, methods for importing/exporting diagram representations, and manipulations
* TetOverlay - equivalent of TetField, for overlaying on top of TetFields (class exists so later it can be used to generate overlays for Tspins, etc)
* TetSolution - basic sfinder results, setup.html is parsed for these
* TetSetup - TetSolution + continuations (either further TetSetup bags/steps or PCs)
"""

import sfinder


class TetField:
    """Simple implementation of Tetris matrix, no colors, just filled and empty blocks."""

    def __init__(self, fromstring):
        """Generates matrix from field diagram.
        
        Note that in input, rows are NOT separated by newlines (html processing strips <br> elements).
        """
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

    def __init__(self, field_str, fumen, sequence):
        """Fieldstr is the field diagram output by sfinder (not separated by newlines).
        fumens is a list of (fumen_str, sequence) tuples, where fumen_str is the link/data that can be imported by fumen
        """
        self.field = TetField(field_str)
        self.fumen = fumen
        self.sequence = sequence
        #self.PC_rate = None

    #honestly have no idea which class this shoud be in
    def addOverlay(self, tetOverlay):
        return self.field.addOverlay(tetOverlay.overlay)

    def get_remaining_pieces(self):
        """Takes a piece sequence and returns an sfinder piece selector containing the missing pieces + *p7"""
        nextPieces = "*p7"
        remaining = ','.join(set("LJSZIOT") - set(self.sequence))
        if remaining:
            nextPieces = remaining + "," + nextPieces
        return nextPieces

    def tostring(self):
        ret = self.field.tostring()
        ret += "\n\nFumen: %s\n" % self.fumen
        #if self.PC_rate is not None:
        #    ret += " (%s%%)" % self.PC_rate
        return ret


class TetSetup:
    """Collection of solutions filtered to fit a certain specification."""

    def __init__(self, solution):
        self.solution = solution
        self.continuations = []
        self.PC_rate = 0.00
        #self.depth?

    def addContinuations(self, setups):
        #print("Adding %d continations" % len(setups))
        if setups is not None and len(setups) > 0:
            #map is because this is passed TetSolutions (need to fix this?)
            self.continuations.extend(map(TetSetup, setups))
            return True
        else:
            return False

    def findPCs(self, sf):
        """Find PCs for all continuations, then figure out overall PC rate.
        
        Returns true if overall PC rate is > 0.00, for filtering.
        """
        if len(self.continuations) > 0:
            # find PCs for all continuations, filter out continuations without PCs
            self.continuations = list(
                filter(lambda cont: cont.findPCs(sf), self.continuations))
            if len(self.continuations) == 0:
                # no PCs found
                self.PC_rate = 0.00
                return False
            self.PC_rate = sum(
                map(lambda cont: cont.PC_rate, self.continuations)) / len(
                    self.continuations)
        else:
            self.PC_rate = float(
                sf.percent(self.solution.fumen,
                           self.solution.get_remaining_pieces(),
                           str(self.solution.field.height)))
        return self.PC_rate > 0.00

    def tostring(self, cont=False):
        """Pretty print for outputing to results txt file."""
        ret = self.solution.tostring()
        if len(self.continuations) > 0:
            ret += "Continuations:\n"
            for cont in sorted(
                    self.continuations,
                    key=(lambda cont: cont.PC_rate),
                    reverse=True):
                # todo: i think i need to recurse all the way down for 4bag PCs, also don't display % for non-PC results
                ret += "%s (%.2f%%)\n" % (cont.solution.fumen, cont.PC_rate)
        return ret