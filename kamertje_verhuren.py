CORNER = '\u254B'
VERT_WALL = '\u2503'
HOR_WALL = '\u2501'
NO_WALL = '\u00B7'


def parseCoordLine(line):
    return map(int, line.split(' '))


def parsePuzzleLine(line, length):
    for i, char in enumerate(line):
        try:
            yield int(char)
        except ValueError:
            yield None
    for j in range(i, length-1):
        yield None


def wallChar(wallDatum, char):
    if wallDatum is None:
        return ' '
    elif wallDatum:
        return char
    else:
        return NO_WALL


def cellChar(cellDatum):
    if cellDatum is None:
        return ' '
    else:
        return str(cellDatum)


def topRow(data):
    for item in data:
        yield CORNER
        yield wallChar(item, HOR_WALL)
    yield CORNER


def cellRow(leftWallData, cellData):
    for i, cell in enumerate(cellData):
        yield wallChar(leftWallData[i], VERT_WALL)
        yield cellChar(cell)
    yield wallChar(leftWallData[i+1], VERT_WALL)


class Wall:
    '''
    Access helper for the wall table.
    A wall is either True, False or None (unknown)
    '''

    def __init__(self, puzzle, row, col, leftWall):
        self.puzzle = puzzle
        self.row = row
        self.col = col
        self.leftWall = leftWall

    def getValue(self):
        if (self.leftWall):
            return self.puzzle.leftWalls[self.row][self.col]
        else:
            return self.puzzle.topWalls[self.row][self.col]

    def setValue(self, newValue):
        if (self.leftWall):
            self.puzzle.leftWalls[self.row][self.col] = newValue
        else:
            self.puzzle.topWalls[self.row][self.col] = newValue

class SomethingWithWalls:
    def __init__(self, walls):
        self.walls = walls

    def undecidedWalls(self):
        return [wall for wall in self.walls if wall.getValue() is None]

    def realWalls(self):
        return [wall for wall in self.walls if wall.getValue() is True]

    def notWalls(self):
        return [wall for wall in self.walls if wall.getValue() is False]

class Corner(SomethingWithWalls):
    '''The corner is referenced as the corner in the top-left corner of the corresponding cell'''
    def __init__(self, puzzle, row, col):
        walls = []
        if row > 0:
            # above
            walls.append(Wall(puzzle, row=row-1, col=col, leftWall=True))
        if row < puzzle.height:
            # below
            walls.append(Wall(puzzle, row=row, col=col, leftWall=True))
        if col > 0:
            # left
            walls.append(Wall(puzzle, row=row, col=col-1, leftWall=False))
        if col < puzzle.width:
            # right
            walls.append(Wall(puzzle, row=row, col=col, leftWall=False))
        super().__init__( walls)

    def isFulfilled(self):
        return len(self.undecidedWalls()) == 0

class Cell(SomethingWithWalls):
    def __init__(self, puzzle, row, col):
        self.puzzle = puzzle
        self.row = row
        self.col = col
        walls = [
            #Top
            Wall(self.puzzle, row=self.row, col=self.col, leftWall=False),
            #Right
            Wall(self.puzzle, row=self.row, col=self.col+1, leftWall=True),
            #Bottom
            Wall(self.puzzle, row=self.row+1, col=self.col, leftWall=False),
            #Left
            Wall(self.puzzle, row=self.row, col=self.col, leftWall=True)
        ]
        super().__init__( walls)

    def getValue(self):
        return self.puzzle.rows[self.row][self.col]

    def fulfilled(self):
        if self.getValue() is None:
            return True
        else:
            return len(self.undecidedWalls()) == 0

    def __str__(self):
        return '({},{}): {}'.format(self.row, self.col, [w.getValue() for w in self.walls])

class KamertjeVerhuren:
    @staticmethod
    def parse(stream):
        rows = []  # array of arrays of letters. Space is empty
        topWalls = None
        leftWalls = None
        for line in stream:
            if not line.startswith('#'):
                line = line.strip('\n')
                if line in ['size', 'puzzle', 'top', 'left']:
                    section = line
                elif section == 'size':
                    width, height = parseCoordLine(line)
                elif section == 'puzzle':
                    rows.append(list(parsePuzzleLine(line, width)))
                elif section == 'top':
                    if topWalls is None:
                        topWalls = [[None for _ in range(width)] for _ in range(height + 1)]
                    row, col = parseCoordLine(line)
                    topWalls[row][col] = True
                elif section == 'left':
                    if leftWalls is None:
                        leftWalls = [[None for _ in range(width + 1)] for _ in range(height)]
                    row, col = parseCoordLine(line)
                    leftWalls[row][col] = True
        return KamertjeVerhuren(width, height, rows, topWalls, leftWalls)

    def __init__(self, width, height, rows, topWalls, leftWalls):
        self.width = width
        self.height = height
        self.rows = rows
        self.topWalls = topWalls
        self.leftWalls = leftWalls

        self.allCells = [Cell(self, row, col) for row in range(self.height) for col in range(self.width)]
        self.allCorners = [Corner(self, row, col) for row in range(self.height+1) for col in range(self.width+1)]
        self.cleanUp()

        def cellUnknownsAllWalls():
            changes = 0
            for cell in self.allCells:
                if cell.getValue() is not None and cell.getValue() == len(cell.undecidedWalls()) + len(cell.realWalls()):
                    for wall in cell.undecidedWalls():
                        wall.setValue(True)
                        changes += 1
            return changes

        def cellUnknownsAllEmpties():
            changes = 0
            for cell in self.allCells:
                if cell.getValue() is not None and cell.getValue() == len(cell.realWalls()):
                    for wall in cell.undecidedWalls():
                        wall.setValue(False)
                        changes += 1
            return changes

        def cornerWallInMeansWallOut():
            changes = 0
            for corner in self.allCorners:
                if len(corner.realWalls()) == 1 and len(corner.undecidedWalls()) == 1:
                    corner.undecidedWalls()[0].setValue(True)
                    changes += 1
            return changes

        def cornerNoWallInMeansNoWallOut():
            changes = 0
            for corner in self.allCorners:
                if len(corner.realWalls()) == 0 and len(corner.undecidedWalls()) == 1:
                    corner.undecidedWalls()[0].setValue(False)
                    changes += 1
            return changes

        def cornerMaxTwoWalls():
            changes = 0
            for corner in self.allCorners:
                if len(corner.realWalls()) == 2:
                    for wall in corner.undecidedWalls():
                        wall.setValue(False)
                        changes += 1
            return changes

        self.rules = [
            cellUnknownsAllWalls,
            cellUnknownsAllEmpties,
            cornerWallInMeansWallOut,
            cornerNoWallInMeansNoWallOut,
            cornerMaxTwoWalls
        ]

    def cleanUp(self):
        '''Some checks to do after each applied rule, to get rid of data that we no longer need to check each time '''
        self.allCells = [cell for cell in self.allCells if not cell.fulfilled()]

    def solved(self):
        self.cleanUp()
        #todo: also check validity
        return len(self.allCells) == 0

    def corners(self):
        '''Iterates the corners of the puzzle, and for each corner gives the state of its connected walls'''
        pass

    def getState(self):
        ans = []
        for i in range(self.height):
            ans.append(''.join(topRow(self.topWalls[i])))
            ans.append(''.join(cellRow(self.leftWalls[i], self.rows[i])))
        ans.append(''.join(topRow(self.topWalls[i+1])))
        return '\n'.join(ans)

    def getStats(self):
        return '{} cells to fulfil:{}'.format(len(self.allCells), [(c.row, c.col, c.getValue()) for c in self.allCells])


