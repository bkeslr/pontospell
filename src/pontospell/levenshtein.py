#! /usr/bin/env python3

"""levenshtein.py - a module for computing minimum string edit distance.

Brett Kessler, Washington University in St. Louis

>>> from pontospell.levenshtein import Levenshtein
>>> lev = Levenshtein()
>>> lev.set_pair('intention', 'execution')
8.0
>>> lev.min_edit_distance()
8.0
>>> print(lev.alignment())
i >    1
n ~ e  2
t ~ x  2
e = e  0
  < c  1
n ~ u  2
t = t  0
i = i  0
o = o  0
n = n  0

Default engine is set up to give a cost of 1 to all insertions and deletions,
2 to all nonidentical substitutions. To change these values, inherit the
Levenshtein class and override these methods, which return a numeric
value for the cost:

ins_cost(self, element)
del_cost(self, element)
sub_cost(self, sequence1, sequence2)

The last should return 0 for identical elements, but that can be changed if
you are not concerned that what the algorithm finds are technically
distances.

"""

from typing import Any, Dict, List, NamedTuple, Sequence, Tuple
import unicodedata

VERSION = '0.2'

START = 'start'
INSERT = 'i'
DELETE = 'd'
SUBSTITUTE = 's'

# pylint: disable=invalid-name
AlignmentUnit = NamedTuple(
    'AlignmentUnit', [('unit1', str), ('unit2', str), ('cost', float)])
AlignmentUnits = List[AlignmentUnit]
Coordinates = Tuple[int, int]
# pylint: enable=invalid-name

def print_len(text: str) -> int:
    """Return length of text in characters, excluding Mark characters.

    This is meant to approximate width of text in
    a monospaced font, so that a plaintext table has a decent
    chance of lining up the columns correctly.

    >>> print_len('abc')
    3

    'é' counts as one display character, whether it is represented as a single
    precombined Unicode character or as a letter character followed by an
    diacritic character.
    >>> print_len('abb\N{LATIN SMALL LETTER E WITH ACUTE}')
    4
    >>> print_len('abbe\N{COMBINING ACUTE ACCENT}')
    4

    """
    width = 0
    for character in str(text):
        if not unicodedata.category(character).startswith('M'):
            width += 1
    return width

def greatest_width(elements: List[str]) -> int:
    """Return the printing length of the longest string in the list.

    >>> greatest_width(['a', 'á', 'ȩ̀'])
    1
    """
    widest: int = 0
    for element in elements:
        widest = max(widest, print_len(element))
    return widest


class Cell:
    """A cell in a distance matrix.

    Each element tells the cumulative cost
    of getting to this point in the table (.num) and what operation
    was taken to get here – SUBSTITUTE, DELETE, or INSERT.
    The value START is used always and only in the upper left cell (0, 0).
    """
    def __init__(self: 'Cell', num: float, operation: str) -> None:
        self.num: float = num
        self.operation: str = operation


class Levenshtein:
    """An engine for computing string-edit distance.

    The object keeps state for each comparison until a new pair of comparanda
    is set.

    self.set_pair(sequence1, sequence2) - which strings to compare.
    self.min_edit_distance() - value for last-set pair of strings
    self.table(stream) - writes to Output stream a plaintext
        table showing numbers and best operation for each cell.
    self.alignment() - returns string showing optimal alignment
    self.alignment_facts() - returns list of tuples showing alignment
        in more programmatic form

    """

    def __init__(self: 'Levenshtein') -> None:
        self.sequence1: list = []
        self.sequence2: list = []
        self.distance: Dict[Coordinates, Cell] = None
        self.widest_sequence1_char: int = None
        self.widest_sequence2_char: int = None

    def set_pair(self: 'Levenshtein', sequence1: Sequence, sequence2: Sequence
                ) -> float:
        """Compares the two items and returns the distance between them.

        Arguments can be strings, in which case their characters are the units
        of comparison.
        They may also be sequences of arbitrary objects.
        The latter can be useful if your letters are more complicated than
        Unicode affords.
        For example, the tradition of several writing systems treats
        digraphic phonograms as individual letters, so you may want to do
        so as well. Welsh treats 'ch' and 'll' as individual letters. Naively:
        >>> lev = Levenshtein()
        >>> lev.set_pair('llach', 'llam')
        3.0
        >>> print(lev.alignment())
        l = l  0
        l = l  0
        a = a  0
        c >    1
        h ~ m  2

        Using lists of letters:
        >>> lev.set_pair(['ll', 'a', 'ch'], ['ll', 'a', 'm'])
        2.0
        >>> print(lev.alignment())
        ll = ll  0
         a =  a  0
        ch ~  m  2

        Sequences don’t even have to contain strings:
        >>> lev.set_pair([6, 78, 5], [6, 79, 5])
        2.0
        >>> print(lev.alignment())
         6 =  6  0
        78 ~ 79  2
         5 =  5  0
        """
        self.sequence1 = list(sequence1)
        self.sequence2 = list(sequence2)
        self.widest_sequence1_char = greatest_width(self.sequence1)
        self.widest_sequence2_char = greatest_width(self.sequence2)
        return self._compute_min_edit_distance()

    def ins_cost(self: 'Levenshtein', element2: Any) -> float:
        """Return the cost of this element being in sequence2 but not sequence1.

        Override this if you wish to change the cost of an
        insertion. It is possible to tailor this so that different
        costs are associated with different insertions. For example, to
        assign a much lower cost to inserting a non-letter character than
        to inserting a letter:
        >>> class LevenshteinPlus(Levenshtein):
        ...     def ins_cost(self, element2):
        ...         return (
        ...             1 if unicodedata.category(element2).startswith('L')
        ...             else 0.2)
        >>> lev = LevenshteinPlus()
        >>> lev.set_pair('cowgirl', 'cow-girls')
        1.2
        >>> print(lev.alignment())
        c = c  0
        o = o  0
        w = w  0
          < -  0.2
        g = g  0
        i = i  0
        r = r  0
        l = l  0
          < s  1
        """
        #pylint: disable=unused-argument,no-self-use
        return 1

    def del_cost(self: 'Levenshtein', element1: Any) -> float:
        """Return the cost of this element being in sequence1 but not sequence2.

        Override this if you wish to change the cost of a deletion.
        For example, to assign a much lower cost to deleting a ^ diacritic
        than a letter:
        >>> from unicodedata import normalize
        >>> class LevenshteinPlus(Levenshtein):
        ...     def del_cost(self, element1):
        ...         return (
        ...             0.3 if element1 == '\N{COMBINING CIRCUMFLEX ACCENT}'
        ...             else 1)
        >>> lev = LevenshteinPlus()
        >>> lev.set_pair(normalize('NFD', 'être'), 'etr')
        1.3
        >>> print(lev.alignment())
        e = e  0
        ̂ >    0.3
        t = t  0
        r = r  0
        e >    1
        """
        #pylint: disable=unused-argument,no-self-use
        return 1

    def sub_cost(self: 'Levenshtein', element1: Any, element2: Any) -> float:
        """Return the cost of matching element1 in sequence1 with element2 in
        sequence2.

        Override this if you wish to change the cost of substitutions.
        For example, one might want to decrease the cost of a mismatch from 2,
        which is the same as deleting one element then inserting another.
        One might consider setting it to 1, the same as other operations;
        or to some intermediate value, such as √2, the Euclidean distance
        between an orthogonal insertion (1) and a deletion (1):
        >>> from math import sqrt
        >>> class LevenshteinPlus(Levenshtein):
        ...     def sub_cost(self, element1, element2):
        ...         return 0 if element1 == element2 else sqrt(2)
        >>> lev = LevenshteinPlus()
        >>> lev.set_pair('bard', 'bart')
        1.4142135623730951
        >>> print(lev.alignment())
        b = b  0
        a = a  0
        r = r  0
        d ~ t  1.4142135623730951
        """
        #pylint: disable=no-self-use
        return 0 if element1 == element2 else 2

    def _compute_min_edit_distance(self: 'Levenshtein') -> float:
        sequence2 = self.sequence2
        sequence1 = self.sequence1

        # Initialize margins of distance matrix:
        self.distance = distance = {(0, 0): Cell(0.0, START)}
        for targ_pos, targ_element in enumerate(sequence2):
            i = targ_pos + 1
            distance[i, 0] = Cell(
                distance[targ_pos, 0].num + self.ins_cost(targ_element),
                INSERT)
        for src_pos, src_element in enumerate(sequence1):
            j = src_pos + 1
            distance[0, j] = Cell(
                distance[0, src_pos].num + self.del_cost(src_element),
                DELETE)

        # Compute body of distance matrix:
        for targ_pos, targ_element in enumerate(sequence2):
            i = targ_pos + 1
            for src_pos, src_element in enumerate(sequence1):
                j = src_pos + 1
                ins_cost = (
                    distance[targ_pos, j].num +
                    self.ins_cost(targ_element))
                sub_cost = (
                    distance[targ_pos, src_pos].num +
                    self.sub_cost(src_element, targ_element))
                del_cost = (
                    distance[i, src_pos].num +
                    self.del_cost(src_element))
                min_cost = min(ins_cost, sub_cost, del_cost)
                distance[i, j] = Cell(
                    min_cost,
                    SUBSTITUTE if min_cost == sub_cost else
                    DELETE if min_cost == del_cost else
                    INSERT)
        return self.min_edit_distance()

    def min_edit_distance(self: 'Levenshtein') -> float:
        """Return the distance between sequence1 and sequence2.

        Uses the dynamic programming matrix cached from the most recent
        set_pair(), and so should return the same distance.
        >>> lev = Levenshtein()
        >>> lev.set_pair('intention', 'execution')
        8.0
        >>> lev.min_edit_distance()
        8.0
        """
        return self.distance[len(self.sequence2), len(self.sequence1)].num

    def alignment_facts(self: 'Levenshtein') -> AlignmentUnits:
        """Show an optimal alignment as a list of AlignmentUnit.

        Each AlignmentUnit is (unit1, unit2, cost),
        where unit1 can be None (insertion) and unit2
        can be None (deletion). cost tells cumulative cost.
        Works by backtracing from the last cell – where sequence1 is
        totally consumed and sequence2 totally generated – back to
        the origin.

        >>> lev = Levenshtein()
        >>> lev.set_pair('dag', 'doge')
        3.0
        >>> from pprint import pprint
        >>> pprint(lev.alignment_facts())
        [AlignmentUnit(unit1='d', unit2='d', cost=0.0),
         AlignmentUnit(unit1='a', unit2='o', cost=2.0),
         AlignmentUnit(unit1='g', unit2='g', cost=2.0),
         AlignmentUnit(unit1=None, unit2='e', cost=3.0)]
        """
        backtrace: AlignmentUnits = []
        sequence1 = self.sequence1
        sequence2 = self.sequence2
        distance = self.distance
        position1 = len(sequence1)
        position2 = len(sequence2)
        while position1 > 0 or position2 > 0:
            cell = distance[position2, position1]
            provenance = cell.operation
            cost = cell.num
            if provenance == SUBSTITUTE:
                position1 -= 1
                position2 -= 1
                s_char = sequence1[position1]
                t_char = sequence2[position2]
                backtrace.insert(0, AlignmentUnit(s_char, t_char, cost))
            elif provenance == INSERT:
                position2 -= 1
                t_char = sequence2[position2]
                backtrace.insert(0, AlignmentUnit(None, t_char, cost))
            else:  # provenance == DELETE:
                position1 -= 1
                s_char = sequence1[position1]
                backtrace.insert(0, AlignmentUnit(s_char, None, cost))
        return backtrace

    def alignment(self: 'Levenshtein') -> str:
        """Return the alignment as a printable plaintext string.

        Each alignment is separated from the following by a newline.
        It shows sequence1 character (white space if insertion),
        operation (< for insertion, > for deletion, ~ for substitution,
        = for no change), sequence2 character (white space if deletion),
        and cost of the operation.
        >>> lev = Levenshtein()
        >>> lev.set_pair('dag', 'doge')
        3.0
        >>> print(lev.alignment())
        d = d  0
        a ~ o  2
        g = g  0
          < e  1
        """
        backtrace: AlignmentUnits = self.alignment_facts()
        lines: List[str] = []
        formatting = '%%%is %%s %%%is  %%s' % (
            self.widest_sequence1_char, self.widest_sequence2_char)
        prev_cost: float = 0.0
        for unit1, unit2, cum_cost in backtrace:
            cost = cum_cost - prev_cost
            print_cost: str = str(int(cost) if cost % 1 == 0 else cost)
            lines.append(formatting % (
                (unit1 or ' '),
                ('>' if unit2 is None else
                 '<' if unit1 is None else
                 '=' if unit1 == unit2 else
                 '~'),
                (unit2 or ' '),
                print_cost))
            prev_cost = cum_cost
        return '\n'.join(lines)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
