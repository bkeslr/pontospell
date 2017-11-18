# developed under python 3.6.3 from anaconda
""" align.py

Align and score two sequences using dynamic programming.

>>> import pontospell.chart as chart
>>> result = chart.levenshtein('intention', 'execution')
>>> chart.min_edit_distance(result)
8
>>> print(chart.vertical_alignment(result))
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

Preparsing spellings into language-specific letters:
>>> result = chart.levenshtein(['ll', 'a', 'dd'], ['ll', 'a'])
>>> print(chart.vertical_alignment(result))
ll = ll  0
a  = a   0
dd >     1

The default configuration uses Levenshtein’s original operation costs.
You can also pass in functions that define other scores for insertions
(intrusive letters), deletions (omissions of required letters), and
substitutions.
These functions can be parameterized for different characters.
For example, you could treat omitting diacritics and punctuation as less
important than omitting letters.
To assign a much lower cost to inserting a non-letter character than to
inserting a letter:
>>> import unicodedata
>>> def my_ins_cost(insertion):
...     return 1 if unicodedata.category(insertion).startswith('L') else 0.2
>>> result = chart.levenshtein('cowgirl', 'cow-girls', ins_costs=my_ins_cost)
>>> print(chart.vertical_alignment(result))
c = c  0
o = o  0
w = w  0
  < -  0.2
g = g  0
i = i  0
r = r  0
l = l  0
  < s  1

For beginning spellers, it may be useful to score as at least partially correct
phonograms that spell target phonemes in the writing system, even if not
correct in the current word.
For example, spelling English [kæt] as ‹kat› is not as good as ‹cat›, but it is
better than ‹rat›.
One way to approach such a system is to pass in pronunciation as the `source`
sequence, the subject’s spelling as the `target` sequence, and a mapping from
phonemes to phonograms to costs as the core of a `sub_costs` argument.
"""
# Brett Kessler, Washington University in St. Louis, Psychology
# http://spell.psychology.wustl.edu

from enum import Enum
from typing import (
    Any, Callable, Dict, Iterator, List, NamedTuple, NewType, Sequence, Tuple)
import unicodedata

                                                  #pylint: disable=invalid-name
SeqPos = int
class Coordinates(NamedTuple):
    """ Coordinates of a position in the distance matrix. """
    target_pos: int
    source_pos: int
Cost = float
class Operation(Enum):
    """ String edit operation types. """
    START = 'start'
    INS = 'i'
    DEL = 'd'
    SUB = 's'
class Cell(NamedTuple):
    """ One cell in matrix. """
    this_cost: Cost
    cumulative_cost: Cost
    operation: Operation
DistanceMatrix = NewType('DistanceMatrix', Dict[Coordinates, Cell])
InsertCostFunction = Callable[[Any], Cost]
DeleteCostFunction = Callable[[Any], Cost]
SubstituteCostFunction = Callable[[Any, Any], Cost]
class PairAnalysis(NamedTuple):
    """ Results of a string-edit analysis. """
    source: Sequence
    source_widest: int
    target: Sequence
    target_widest: int
    ins_cost: InsertCostFunction
    del_cost: DeleteCostFunction
    sub_cost: SubstituteCostFunction
    matrix: DistanceMatrix = DistanceMatrix(
        {Coordinates(0, 0): Cell(0, 0, Operation.START)})
class EditStep(NamedTuple):
    """ One step in string-edit path. """
    source: Any
    target: Any
    cell: Cell
Backtrace = NewType('Backtrace', List[EditStep])
                                                  #pylint: enable=invalid-name

def print_len(elements: Any) -> int:
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
    return sum(
        1 for element in str(elements)
        if not unicodedata.category(element).startswith('M'))

def greatest_width(elements: Sequence) -> int:
    """Return the printing length of the longest string in the sequence.

    >>> greatest_width(['a', 'á', 'ȩ̀'])
    1
    """
    return max(print_len(element) for element in elements)

def enumerate1(seq: Sequence) -> Iterator[Tuple[SeqPos, Any]]:
    """ Like `enumerate`, but starts at 1. """
    zero_based: SeqPos
    anything: Any
    for zero_based, anything in enumerate(seq):
        yield zero_based + 1, anything

def make_edited_cell(
        analysis: PairAnalysis, to_coords: Coordinates,
        src_element: Any, targ_element: Any) -> Cell:
    """ Make new cell in dynamic programming matrix. """
    opus: Operation = (Operation.INS if src_element is None
                       else Operation.DEL if targ_element is None
                       else Operation.SUB)
    coords_before = Coordinates(
        to_coords.target_pos - (1 if targ_element is not None else 0),
        to_coords.source_pos - (1 if src_element is not None else 0))
    cell_before: Cell = analysis.matrix[coords_before]
    cumul_cost_before: Cost = cell_before.cumulative_cost
    new_cost: Cost = (
        analysis.ins_cost(targ_element) if opus == Operation.INS
        else analysis.del_cost(src_element) if opus == Operation.DEL
        else analysis.sub_cost(src_element, targ_element))
    return Cell(new_cost, cumul_cost_before + new_cost, opus)

def compute_min_edit_distance(analysis: PairAnalysis) -> None:
    """ Fill out the dynamic programming matrix for this analysis. """
    targ_pos: SeqPos
    targ_element: Any
    # Initialize margins of distance matrix:
    for targ_pos, targ_element in enumerate1(analysis.target):
        coords = Coordinates(targ_pos, 0)
        analysis.matrix[coords] = make_edited_cell(
            analysis, coords, None, targ_element)
    src_pos: SeqPos
    src_element: Any
    for src_pos, src_element in enumerate1(analysis.source):
        coords = Coordinates(0, src_pos)
        analysis.matrix[coords] = make_edited_cell(
            analysis, coords, src_element, None)
    # Compute body of distance matrix:
    for targ_pos, targ_element in enumerate1(analysis.target):
        for src_pos, src_element in enumerate1(analysis.source):
            coords = Coordinates(targ_pos, src_pos)
            ins_cell: Cell = make_edited_cell(
                analysis, coords, None, targ_element)
            sub_cell: Cell = make_edited_cell(
                analysis, coords, src_element, targ_element)
            del_cell: Cell = make_edited_cell(
                analysis, coords, src_element, None)
            min_cost: Cost = min(
                c.cumulative_cost for c in (ins_cell, sub_cell, del_cell))
            cell: Cell = (sub_cell if min_cost == sub_cell.cumulative_cost
                          else del_cell if min_cost == del_cell.cumulative_cost
                          else ins_cell)
            analysis.matrix[coords] = cell

def lev_ins_function(targ_element: Any) -> Cost:
    """ Return the cost of inserting this element.

    Per Levenshtein, this is 1 regardless of what the element is.
    """
    #pylint: disable=unused-argument
    return 1

def lev_del_function(src_element: Any) -> Cost:
    """ Return the cost of deleting this element, per Levenshtein.

    Per Levenshtein, this is 1 regardless of what the element is.
    """
    #pylint: disable=unused-argument
    return 1

def lev_sub_function(src_element: Any, targ_element: Any) -> Cost:
    """Return the cost of replacing source element with target element.

    By definition, distance is 0 if the two elements are the same.
    """
    #pylint: disable=unused-argument
    return 0 if src_element == targ_element else 2

def levenshtein(source: Sequence, target: Sequence,
                ins_costs: InsertCostFunction = lev_ins_function,
                del_costs: DeleteCostFunction = lev_del_function,
                sub_costs: SubstituteCostFunction = lev_sub_function
               ) -> PairAnalysis:
    """ Compare two sequences and return analysis. """
    analysis = PairAnalysis(
        source, greatest_width(source), target, greatest_width(target),
        ins_costs, del_costs, sub_costs)
    compute_min_edit_distance(analysis)
    return analysis

def min_edit_distance(analysis: PairAnalysis) -> Cost:
    """ Return the minimal string edit distance as shown in matrix. """
    coords: Coordinates = Coordinates(
        len(analysis.target), len(analysis.source))
    last_cell: Cell = analysis.matrix[coords]
    return last_cell.cumulative_cost

def get_one_backtrace(analysis: PairAnalysis) -> Backtrace:
    """Return a list of tuples showing an optimal alignment.

    Works by backtracing from the last cell – where input is
     totally consumed and output totally generated – back to
     the origin.
    """
    src_pos: SeqPos = len(analysis.source)
    targ_pos: SeqPos = len(analysis.target)
    backtrace = Backtrace([])
    while src_pos > 0 or targ_pos > 0:
        cell: Cell = analysis.matrix[Coordinates(targ_pos, src_pos)]
        if cell.operation == Operation.SUB:
            src_pos -= 1
            targ_pos -= 1
            backtrace.insert(0, EditStep(
                analysis.source[src_pos],
                analysis.target[targ_pos],
                cell))
        elif cell.operation == Operation.INS:
            targ_pos -= 1
            backtrace.insert(0, EditStep(
                None,
                analysis.target[targ_pos],
                cell))
        else:  # DEL
            src_pos -= 1
            backtrace.insert(0, EditStep(
                analysis.source[src_pos],
                None,
                cell))
    return backtrace

def vertical_alignment(analysis: PairAnalysis) -> str:
    """ Return the alignment as a printable plaintext string.

    Each alignment is separated from the following by a newline.
    It shows source character (white space if insertion),
    operation (< for insertion, > for deletion, ~ for substitution,
    = for no change), target character (white space if deletion),
    and cost of the operation.
    """
    backtrace: Backtrace = get_one_backtrace(analysis)
    lines: List[str] = []
    step: EditStep
    for step in backtrace:
        source = f"{(step.source or ' '):<{analysis.source_widest}}"
        operator: str = {
            Operation.DEL: '>',
            Operation.INS: '<',
            Operation.SUB: '=' if step.source == step.target else '~'
            }[step.cell.operation]
        target = f"{(step.target or ' '):<{analysis.target_widest}}"
        lines.append(
            f'{source} {operator} {target}  {step.cell.this_cost}')
    return '\n'.join(lines)

# Local Variables:
# mode: python
# indent-tabs-mode: nil
# tab-width: 4
# coding: utf-8-unix
# End:
