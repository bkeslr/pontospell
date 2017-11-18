#! /usr/bin/env python
# developed under 3.6.3

""" test_xducer.py

Tests for xducer module, using pytest.
"""

# Brett Kessler, Washington University in St. Louis
# http://spell.psychology.wustl.edu/bkessler.html

from sys import stderr
from typing import Set

#import pytest  # type: ignore

import pontospell.xducer as px

def test_intention(capsys) -> None:
    """ Try a basic comparison. """
    result: px.Parses = px.relate(px.arguments('intention', 'execution'))
    assert len(result) == 134  #pylint: disable=len-as-condition
    print(px.vertical_align(result[0]))
    out: str
    out, _ = capsys.readouterr()
    assert out == '''\
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
'''
    parse: px.Parse
    assert all(px.parse_cost(parse) == 8 for parse in result)
    # Assert that all the parses are different from each other.
    set_of_parses: Set[str] = set()
    for parse in result:
        representation: str = px.vertical_align(parse)
        if representation in set_of_parses:
            print('Duplicated: {representation}', file=stderr)
        else:
            set_of_parses.add(representation)
    assert len(set_of_parses) == 134

def test_just_one(capsys) -> None:
    """ Test `just_one` option. """
    result: px.Parses = px.relate(
        px.arguments('intention', 'execution', just_one=True))
    assert len(result) == 1
    parse: px.Parse = result[0]
    print(px.vertical_align(parse))
    out, _ = capsys.readouterr()
    assert out == '''\
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
'''

def test_identical(capsys) -> None:
    """ Match identical strings; should be only 1 parse. """
    result: px.Parses = px.relate(px.arguments('intention', 'intention'))
    assert len(result) == 1
    parse: px.Parse = result[0]
    print(px.vertical_align(parse))
    out, _ = capsys.readouterr()
    assert out == '''\
i = i  0
n = n  0
t = t  0
e = e  0
n = n  0
t = t  0
i = i  0
o = o  0
n = n  0
'''

def test_empties() -> None:
    """ Match two empty strings. """
    result: px.Parses = px.relate(px.arguments('', ''))
    assert not result

def test_target_empty(capsys) -> None:
    """ Match a string against an empty string. """
    results: px.Parses = px.relate(px.arguments('cat', ''))
    assert len(results) == 1
    parse: px.Parse = results[0]
    print(px.vertical_align(parse))
    out, _ = capsys.readouterr()
    assert out == '''\
c >    1
a >    1
t >    1
'''

def test_source_empty(capsys) -> None:
    """ Match an empty string against a string. """
    results: px.Parses = px.relate(px.arguments('', 'cat'))
    assert len(results) == 1
    parse = results[0]
    print(px.vertical_align(parse))
    out, _ = capsys.readouterr()
    assert out == '''\
  < c  1
  < a  1
  < t  1
'''

def test_list_of_letters(capsys) -> None:
    """ Test sequence of strings rather than plain old strings. """
    src = ['ll', 'a', 'ch']
    targ = ['ll', 'a', 'm']
    results: px.Parses = px.relate(px.arguments(src, targ))
    parse: px.Parse = results[0]
    print(px.vertical_align(parse))
    out, _ = capsys.readouterr()
    assert out == '''\
ll = ll  0
a  = a   0
ch ~ m   2
'''

def test_tuple_of_numbers(capsys) -> None:
    """ Test comparanda that are tuples of numbers. """
    src = (6, 78, 5)
    targ = (6, 79, 5)
    results: px.Parses = px.relate(px.arguments(src, targ))
    parse: px.Parse = results[0]
    print(px.vertical_align(parse))
    out, _ = capsys.readouterr()
    assert out == '''\
6  = 6   0
78 ~ 79  2
5  = 5   0
'''

def test_ins_cost_letters(capsys) -> None:
    """ Change insertion cost to be higher for letters than other symbols. """
    import unicodedata
    def my_ins_cost(insertion):
        """ 1 for letters, 0.2 for other symbols. """
        return 1 if unicodedata.category(insertion).startswith('L') else 0.2
    src = 'cowgirl'
    targ = 'cow-girls'
    costs = px.CostFunctions(insert=my_ins_cost)
    results: px.Parses = px.relate(px.arguments(src, targ, costs=costs))
    parse: px.Parse = results[0]
    assert px.parse_cost(parse) == 1.2
    print(px.vertical_align(parse))
    out, _ = capsys.readouterr()
    assert out == '''\
c = c  0
o = o  0
w = w  0
  < -  0.2
g = g  0
i = i  0
r = r  0
l = l  0
  < s  1
'''
