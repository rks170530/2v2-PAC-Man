import sys
import time
from typing import List, Tuple, Dict


class Literal:
    def __init__(self, string=None, negate=None, name=None):
        if string is not None:
            self.negated: bool = True if '~' in string else False
            self.name: str = string.strip('~')
        elif negate is not None and name is not None:
            self.negated = negate
            self.name = name

    def __str__(self) -> str:
        if self.negated:
            return '~' + self.name
        else:
            return self.name

    def __repr__(self) -> str:
        return (f'{self.__class__.__name__}('
                f'{self.name!r}, {self.negated!r})')

    def __eq__(self, o: 'Literal') -> bool:
        return self.name == o.name and self.negated == o.negated

    def __lt__(self, other):
        return self.name < other.name

    def __hash__(self) -> int:
        return super().__hash__()

    def get_negative(self) -> 'Literal':
        return Literal(name=self.name, negate=not self.negated)


class Clause:
    def __init__(self, literals: List[Literal], derive=()):
        self.literals: List[Literal] = literals  # TODO make dictionary instead
        self.derive: Tuple = derive

    def __str__(self) -> str:
        return ' '.join(str(x) for x in self.literals) + ' {' + ', '.join(str(x) for x in self.derive) + '}'

    def __repr__(self) -> str:
        return (f'{self.__class__.__name__}('
                f'{self.literals!r})')

    def __contains__(self, item: Literal) -> bool:
        for literal in self.literals:
            if item == literal:
                return True
        return False

    def __eq__(self, other: 'Clause') -> bool:
        return self.literals == other.literals

    def equiv(self, o: 'Clause') -> bool:
        long, short = (self.literals, o.literals) if len(self.literals) > len(o.literals) \
            else (o.literals, self.literals)
        for literal in long:
            if literal not in short:
                return False
        return True

    def negate(self) -> List:
        return [Clause([x.get_negative()]) for x in self.literals]

    def simplify(self) -> bool:
        new = []
        count = 0
        for x in self.literals:
            if x not in new:
                y = x.get_negative()
                if y not in self.literals:
                    new.append(x)
                else:
                    if count > 2:
                        return False
                    count += 1
        self.literals = new
        return True


class Resolver:

    def __init__(self, kb: Dict[str, Clause]):
        self.kb: Dict[str, Clause] = kb
        self.negate: Dict[Literal, Literal] = {}
        self.keys = list(self.kb.keys())
        for clause in kb.values():
            for literal in clause.literals:
                n = literal.get_negative()
                self.negate[literal] = n
                self.negate[n] = literal

    def __str__(self) -> str:
        return '\n'.join(str(str(x + 1) + '. ' + str(self.kb[y])) for x, y in enumerate(self.kb))

    def __repr__(self) -> str:
        return (f'{self.__class__.__name__}('
                f'{self.kb!r})')

    def resolve(self) -> bool:
        i = 1
        while i < len(self.kb):
            for j in range(0, i):
                if self.__resolve(i, j):
                    return True
            i += 1
        return False

    def __resolve(self, i: int, j: int) -> bool:
        if i >= len(self.keys):
            self.keys = list(self.kb.keys())
        clause_i = self.kb[self.keys[i]]
        clause_j = self.kb[self.keys[j]]
        for a in clause_i.literals:
            if self.negate[a] in clause_j.literals:
                lists = clause_i.literals + clause_j.literals
                x = Clause(lists, (i + 1, j + 1))
                if not x.simplify():
                    break
                if len(x.literals) == 0:
                    # noinspection PyTypeChecker
                    self.kb['result'] = f'Contradiction {{{i + 1}, {j + 1}}}'
                    return True
                if not self.is_redundant(x):
                    self.kb[str(sorted(x.literals.copy()))] = x
                break
        return False

    def is_redundant(self, c: Clause) -> bool:
        return str(c.literals.copy().sort()) in self.kb


def read_kb(file: str) -> Dict[str, Clause]:
    infile = open(file, "r")
    kb: Dict[str, Clause] = {}
    x = None
    for line in infile:
        line = line.strip().split(" ")
        literals = []
        for x in line:
            literals.append(Literal(x))
        x = Clause(literals)
        kb[str(sorted(x.literals.copy()))] = x
    infile.close()
    for y in kb.pop(str(sorted(x.literals.copy()))).negate():
        kb[str(sorted(y.literals.copy()))] = y
    return kb


if __name__ == "__main__":
    if len(sys.argv) < 1:
        print("Missing arguments")
        sys.exit(1)

    problem = Resolver(read_kb(sys.argv[1]))
    # t0 = time.time()
    valid = problem.resolve()
    # t1 = time.time()
    print(problem)
    print('Valid\n') if valid else print('Fail\n')
    # print(t1 - t0)
