
from collections import defaultdict


def options(size):
    return list(range(1, size+1))


class Cell:
    def __init__(self, size):
        self.options = list(options(size))

    def fulfilled(self):
        return len(self.options) == 1

    def setValue(self, val):
        if val in self.options:
            self.options = [val]
        else:
            raise ValueError('value {} not in options {}',format(val, self.options))

    def getValue(self):
        return self.options[0] if self.fulfilled() else ' '

    def removeOptions(self, values):
        ans = False
        for val in values:
            ans |= self.removeOption(val)
        return ans

    def removeOption(self, val):
        '''Removes the option form this cell, and returns true if it made this cell fulfilled'''
        if val in self.options:
            if len(self.options) > 1:
                self.options.remove(val)
                return True
            else:
                raise ValueError('trying to remove last option {}'.format(val))
        else:
            return False

    def optionsHash(self):
        return str(self.options)

    def __str__(self):
        return str(self.getValue())


class Group:
    def __init__(self):
        self.cells = []

    def add(self, cell):
        self.cells.append(cell)

    def hasAll(self, cells):
        for cell in cells:
            if cell not in self.cells:
                return False
        return True

    def getCandidatesFor(self, number):
        return [c for c in self.cells if number in c.options]

    def unknownNumbers(self):
        knownNumbers = [c.getValue() for c in self.cells if c.fulfilled()]
        return [i for i in options(len(self.cells)) if i not in knownNumbers]

    def check(self):
        changed = 0
        for cell in self.cells:
            if cell.fulfilled():
                value = cell.getValue()
                for otherCell in self.cells:
                    if otherCell is not cell:
                        if otherCell.removeOption(value):
                            changed += 1
        return changed


class Sudoku:
    @staticmethod
    def parse(stream):
        size = None
        rows = []
        groups = defaultdict(Group)
        groupsRead = 0
        rowsRead = 0
        sudokuPuzzle = None
        for line in stream:
            line = line.strip('\r\n')
            if size is None:
                size = len(line)
                for row in range(size):
                    rows.append([Cell(size) for _ in range(size)])
                #initialize the groups for the rows and cols
                for row, rowData in enumerate(rows):
                    for col, cell in enumerate(rowData):
                        groups['row{}'.format(row)].add(cell)
                        groups['col{}'.format(col)].add(cell)
            # read 9 lines that tell which cells are in a group
            if groupsRead < size:
                if len(line) > 0:
                    row = groupsRead
                    for col, char in enumerate(line):
                        group = groups[char]
                        group.add(rows[row][col])
                    groupsRead += 1
                    if groupsRead == size:
                        sudokuPuzzle = Sudoku(rows, groups)
            elif sudokuPuzzle:
                if rowsRead < size: #read 9 lines of rows
                    if len(line) > 0:
                        row = rowsRead
                        for col, char in enumerate(line):
                            try:
                                val = int(char)
                                sudokuPuzzle.setCell(row, col, val)
                            except ValueError:
                                pass
                        rowsRead += 1
        return sudokuPuzzle

    def __init__(self, rows, groups):
        self.rows = rows
        self.groups = groups
        self.options = options(len(self.rows))

        def eachNumberOnlyOnce():
            changed = 0
            for group in self.groups.values():
                for cell in group.cells:
                    if cell.fulfilled():
                        value = cell.getValue()
                        for otherCell in group.cells:
                            if otherCell is not cell:
                                if otherCell.removeOption(value):
                                    changed += 1
            return changed


        def eachNumberAtLeastOnce():
            changed = 0
            for group in self.groups.values():
                for value in group.unknownNumbers():
                    cellsToFulfillValue = group.getCandidatesFor(value)
                    if len(cellsToFulfillValue) == 1:
                        if not cellsToFulfillValue[0].fulfilled():
                            cellsToFulfillValue[0].setValue(value)
                            changed += 1
            return changed

        def makeNOptionsRule(n):
            def nOptionsForNNumbersRulesOutTheRest():
                changed = 0
                for group in self.groups.values():
                    grouping = defaultdict(list)
                    for cell in group.cells:
                        if len(cell.options) == n:
                            grouping[cell.optionsHash()].append(cell)
                    for hash, chosenCells in grouping.items():
                        if len(chosenCells) == n:
                            #set all other cells to 0
                            for cell in group.cells:
                                if cell not in chosenCells:
                                    if cell.removeOptions(chosenCells[0].options):
                                        changed += 1
                return changed
            nOptionsForNNumbersRulesOutTheRest.__name__ = '{0}OptionsFor{0}NumbersRulesOutTheRest'.format(n)
            return nOptionsForNNumbersRulesOutTheRest

        def findGroupOverlaps():
            '''Finds all candidates for a number in one group that are entirely in another group,
            and rules out the rest for the other group '''
            changed = 0
            for groupId, group in self.groups.items():
                for num in group.unknownNumbers():
                    candidates = group.getCandidatesFor(num)
                    if len(candidates) > 1:  # if it is 1, a simpler rule will do its work
                        for otherId, otherGrp in self.groups.items():
                            if otherGrp is not group and otherGrp.hasAll(candidates):
                                for cell in otherGrp.cells:
                                    if cell not in candidates:
                                        if cell.removeOption(num):
                                            changed += 1
            return changed


        self.rules = [
            eachNumberOnlyOnce,
            eachNumberAtLeastOnce,
            makeNOptionsRule(2),
            findGroupOverlaps,
            makeNOptionsRule(3),
            makeNOptionsRule(4),
            makeNOptionsRule(5),
            makeNOptionsRule(6),
            makeNOptionsRule(7)
        ]

    def setCell(self, row, col, val):
        cell = self.rows[row][col]
        cell.setValue(val)

    def solved(self):
        for row in self.rows:
            for cell in row:
                if not cell.fulfilled():
                    return False
        return True

    def getInternalVars(self):
        ansParts = []
        for i in range(1,10):
            def showVal(cell):
                if i in cell.options:
                    if cell.fulfilled():
                        return str(i)
                    else:
                        return ' '
                else:
                    return 'X'
            ansParts.append(['{}:                 '.format(i)] + self.prettyPrint(showVal).splitlines())
        ans = ''
        for line in zip(*ansParts):
            ans += ''.join(line) + '\n'
        return ans

    def prettyPrint(self, cellValue):
        ans = '\u250f\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2513\n'
        for i, row in enumerate(self.rows):
            ans += '\u2503{} {} {}\u2503{} {} {}\u2503{} {} {}\u2503\n'.format(*[cellValue(i) for i in row])
            if (i + 1) % 3 == 0:
                if i < 8:
                    ans += '\u2523\u2501\u2501\u2501\u2501\u2501\u254b\u2501\u2501\u2501\u2501\u2501\u254b\u2501\u2501\u2501\u2501\u2501\u252b\n'
                else:
                    ans += '\u2517\u2501\u2501\u2501\u2501\u2501\u253b\u2501\u2501\u2501\u2501\u2501\u253b\u2501\u2501\u2501\u2501\u2501\u251b\n'
        return ans

    def getState(self):
        return self.prettyPrint(lambda x: str(x)) + '\n' + self.getInternalVars()

