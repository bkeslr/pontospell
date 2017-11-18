# developed under python 3.6.3 from anaconda
""" xducer.py

Align and score two sequences using recursion.

>>> import pontospell.xducer as px
>>> result = px.relate(px.arguments('intention', 'execution'))
>>> len(result)  # number of alignments with same minimal cost
134
>>> first_parse = result[0]
>>> px.parse_cost(first_parse)
8
>>> print(px.vertical_align(first_parse))
i ~ e  2
n ~ x  2
t >    1
e = e  0
n ~ c  2
  < u  1
t = t  0
i = i  0
o = o  0
n = n  0
"""
# Brett Kessler, Washington University in St. Louis, Psychology
# http://spell.psychology.wustl.edu

from enum import Enum
from typing import Any, Callable, Dict, List, NamedTuple, NewType, Sequence

                                                  #pylint: disable=invalid-name
Element = Any
Cost = float
InsCostFunction = Callable[[Element], Cost]
DelCostFunction = Callable[[Element], Cost]
SubCostFunction = Callable[[Element, Element], Cost]
SeqPos = int
""" Zero-based position in source or target sequence """
class Coordinates(NamedTuple):
    """ Starting positions for this and subsequent alignments. """
    source: SeqPos = None
    target: SeqPos = None
class Cell(NamedTuple):
    """ Smallest member of a Parse. An alignment between source and target."""
    source: Any
    target: Any
    this_cost: Cost = 0.0
    cumul_cost: Cost = 0.0
Parse = NewType('Parse', List[Cell])
Parses = NewType('Parses', List[Parse])
class Operation(Enum):
    """ String edit operation: substitute, delete, insert. """
    SUB = 's'  # align a source element with a target element
    DEL = 'd'  # align a source element with nothing
    INS = 'i'  # align a target element with nothing
                                                  #pylint: enable=invalid-name

def lev_ins_function(target: Any) -> Cost:
    """ Levenshtein’s insertion penalty, constant for all elements. """
    #pylint: disable=unused-argument
    return 1

def lev_del_function(source: Any) -> Cost:
    """ Levenshtein’s deletion penalty, constant for all elements. """
    #pylint: disable=unused-argument
    return 1

def lev_sub_function(source: Any, target: Any) -> float:
    """ Levenshtein’s substitution penalty, constant for all pairs. """
    return 0 if source == target else 2

class CostFunctions(NamedTuple):
    """ Functions returning costs of different edit operations. """
    insert: InsCostFunction = lev_ins_function
    delete: DelCostFunction = lev_del_function
    substitute: SubCostFunction = lev_sub_function

class Arguments(NamedTuple):
    """ Arguments for relate command. """
    source: Sequence
    target: Sequence
    cost_functions: CostFunctions
    just_one: bool
    memory: Dict[Coordinates, Parses]

def arguments(source: Sequence,
              target: Sequence,
              costs: CostFunctions = CostFunctions(
                  lev_ins_function, lev_del_function, lev_sub_function),
              just_one: bool = False) -> Arguments:
    """ Arguments in recursive parse. """
    return Arguments(source, target, costs, just_one, {})

def op_cost(args: Arguments, pos: Coordinates, opus: Operation) -> Cost:
    """ Return cost of string-edit operation at this point. """
    return (
        args.cost_functions.substitute(
            args.source[pos.source], args.target[pos.target])
        if opus == Operation.SUB else
        args.cost_functions.delete(args.source[pos.source])
        if opus == Operation.DEL else
        args.cost_functions.insert(args.target[pos.target]))

def parse_cost(pars: Parse) -> Cost:
    """ Return cost of parse (edit series) as a cumulative whole. """
    return pars[0].cumul_cost

def try_op(
        args: Arguments, start_pos: Coordinates, opus: Operation) -> Parses:
    """ Apply operation here, then parse rest of strings. """
    consume_source = 1 if opus in {Operation.DEL, Operation.SUB} else 0
    consume_target = 1 if opus in {Operation.INS, Operation.SUB} else 0
    tail_start = Coordinates(
        start_pos.source + consume_source, start_pos.target + consume_target)
    tail: Parses = relate(args, tail_start)
    cost: Cost = op_cost(args, start_pos, opus)
    cell = Cell(
        args.source[start_pos.source] if consume_source else None,
        args.target[start_pos.target] if consume_target else None,
        cost,
        cost)
    if not tail:
        return Parses([Parse([cell])])
    return Parses([
        Parse([cell._replace(cumul_cost=cell.this_cost + parse_cost(p))] + p)
        for p in tail])

def remove_suboptimal_parses(parses: Parses, just_one: bool) -> Parses:
    """ Return all parses that have same optimal cost. """
    minimum = min(parse_cost(parse) for parse in parses)
    minimal_parses = [parse for parse in parses if parse_cost(parse) == minimum]
    if just_one:
        return Parses([minimal_parses[0]])
    return Parses(minimal_parses)

def parse(args: Arguments, start_pos: Coordinates) -> Parses:
    """ Parse and relate strings from the given starting coordinates. """
    remaining_source: int = len(args.source) - start_pos.source
    remaining_target: int = len(args.target) - start_pos.target
    parses = Parses([])
    if not (remaining_source or remaining_target):
        return parses
    if remaining_source and remaining_target:
        parses.extend(try_op(args, start_pos, Operation.SUB))
    if remaining_source:
        parses.extend(try_op(args, start_pos, Operation.DEL))
    if remaining_target:
        parses.extend(try_op(args, start_pos, Operation.INS))
    if parses:
        parses = remove_suboptimal_parses(parses, args.just_one)
    return parses

def relate(args: Arguments, start: Coordinates = None) -> Parses:
    """ Return optimal alignments between two sequences. """
    if start is None:
        start = Coordinates(0, 0)
    parses: Parses = args.memory.get(start, None)
    if parses is not None:
        return parses
    parses = parse(args, start)
    args.memory[start] = parses
    return parses

def format_cell(cell: Cell, source_widest: int, target_widest: int) -> str:
    """ Make printable representation for vertical alignment. """
    source = f"{(cell.source or ' '):<{source_widest}}"
    operator: str = (
        '>' if cell.target is None else
        '<' if cell.source is None else
        '=' if cell.source == cell.target else
        '~')
    target = f"{(cell.target or ' '):<{target_widest}}"
    return f'{source} {operator} {target}  {cell.this_cost}'

def element_length(cell: Cell, element_name: str) -> int:
    """ Length of element in cell; expect 'source' or 'target' """
    return len(str(getattr(cell, element_name) or ''))

def biggest_length_in_parse(pars: Parse, element_name: str) -> int:
    """ Length of longes element in parse; expect 'source' or 'target' """
    return max(element_length(cell, element_name) for cell in pars)

def vertical_align(pars: Parse) -> str:
    """ Return the alignment as a printable plaintext string.

    Each alignment is separated from the following by a newline.
    It shows source character (white space if insertion),
    operation (< for insertion, > for deletion, ~ for substitution,
    = for no change), target character (white space if deletion),
    and cost of the operation.
    """
    source_widest: int = biggest_length_in_parse(pars, 'source')
    target_widest: int = biggest_length_in_parse(pars, 'target')
    lines: List[str] = [format_cell(cell, source_widest, target_widest)
                        for cell in pars]
    return '\n'.join(lines)

# Local Variables:
# mode: python
# indent-tabs-mode: nil
# tab-width: 4
# coding: utf-8-unix
# End:
