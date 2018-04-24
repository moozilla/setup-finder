"""
'tet' module, contains a bunch of classes used for dealing with Tetris fields, fumen diagrams, and opener specifications
"""

#import sfinder


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

    def outputInputTxt(self, sf):
        sf.setInputTxt(self.field.tostring())

    def findPCs(self, sf, height):
        for fumen in self.fumens:
            fumen.findPC(sf, height)
            pcr = float(fumen.PC_rate)
            if pcr > self.PC_rate:
                self.PC_rate = pcr


class TetFumen:
    """Wrapper for fumen + piece sequence"""

    def __init__(self, fumen, pieces):
        self.fumen = fumen
        self.pieces = pieces
        self.PC_rate = None

    def findPC(self, sf, height):
        """Find PC percent rate. (height and result are strings)"""
        self.PC_rate = sf.percent(
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


def getRemainingPieces(pieces):
    """Takes a piece sequence and returns an sfinder piece selector containing the missing pieces + *p7"""
    nextPieces = "*p7"
    remaining = ','.join(set("LJSZIOT") - set(pieces))
    if remaining:
        nextPieces = remaining + "," + nextPieces
    return nextPieces