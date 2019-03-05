
import sys
from collections import defaultdict

from kamertje_verhuren import KamertjeVerhuren
from sudoku import Sudoku

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = 'puzzels/1.sudoku.txt'
    if filename.endswith('.sudoku.txt'):
        Solver = Sudoku
    elif filename.endswith('.sudokuchaos.txt'):
        Solver = Sudoku
    elif filename.endswith('.kvh.txt'):
        Solver = KamertjeVerhuren
    with open(filename, 'r') as infile:
        solver = Solver.parse(infile)
        print(solver.getState())

        used_rules = defaultdict(int)
        while not solver.solved():
            for rule in solver.rules:
                changes = rule()
                if changes:
                    used_rules[rule.__name__] += changes
                    print('{} caused {} changes'.format(rule.__name__, changes))
                    print('--------------------')
                    print(solver.getState())
                    print('====================')
                    # we want to start over again with rule one
                    break

            if changes == 0:
                #applying rules has no more effect, so stop anyhow
                break

        if solver.solved():
            print('YAYYYYY!')
        else:
            print('Awwwwww...')
        for rule, score in used_rules.items():
            print('{: <30}\t{: >3}'.format(rule, score))