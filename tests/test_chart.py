#! /usr/bin/env python
# developed under 3.6.3

""" test_chart.py

Tests for chart module, using pytest.
"""

# Brett Kessler, Washington University in St. Louis
# http://spell.psychology.wustl.edu/bkessler.html

from math import sqrt
import unicodedata

import pytest  # type: ignore

import pontospell.chart as ponto

def test_coordinates_not_2():
    """ Test run-time errors for Coordinates constructor. """
    with pytest.raises(TypeError):
        ponto.Coordinates(1, 2, 3)
    with pytest.raises(TypeError):
        ponto.Coordinates(1)
    with pytest.raises(TypeError):
        ponto.Coordinates()

def test_print_len():
    """ Test print_len() """
    assert ponto.print_len('a') == 1
    assert ponto.print_len('abc') == 3
    assert ponto.print_len(['a']) == 5
    assert ponto.print_len([('a', 'b'), ('c', 'd')]) == 24
    assert ponto.print_len('e\N{COMBINING CARON}') == 1
    assert ponto.print_len(
        '\N{LATIN SMALL LETTER E WITH CARON}') == 1
    assert ponto.print_len('') == 0

def test_greatest_width():
    """ Test greatest_width() """
    assert ponto.greatest_width(['a', 'á', 'ȩ̀']) == 1
    assert ponto.greatest_width(('a', 'á', 'ȩ̀')) == 1
    with pytest.raises(ValueError):
        ponto.greatest_width([])
    assert ponto.greatest_width('a') == 1
    assert ponto.greatest_width(['a']) == 1
    assert ponto.greatest_width([('a', 'b'), ('cd', 'ef')]) == 12
    with pytest.raises(TypeError):
        ponto.greatest_width(17)

def test_intention_execution():
    """ Test levenshtein('intention', 'execution') """
    result = ponto.levenshtein('intention', 'execution')
    # Example is from Jurafsky & Martin, 2nd ed., p. 73–77.
    assert result is not None
    assert result.source == 'intention'
    assert result.source_widest == 1
    assert result.target == 'execution'
    assert result.target_widest == 1
    assert result.ins_cost == ponto.lev_ins_function
    assert result.del_cost == ponto.lev_del_function
    assert result.sub_cost == ponto.lev_sub_function
    assert len(result.matrix) == (len('intention') + 1) * (len('execution') + 1)
    last_cell = result.matrix[ponto.Coordinates(9, 9)]
    assert last_cell.this_cost == 0
    assert last_cell.cumulative_cost == 8
    assert last_cell.operation == ponto.Operation.SUB
    assert ponto.min_edit_distance(result) == 8
    assert ponto.vertical_alignment(result) == (
        'i >    1\n'
        'n ~ e  2\n'
        't ~ x  2\n'
        'e = e  0\n'
        '  < c  1\n'
        'n ~ u  2\n'
        't = t  0\n'
        'i = i  0\n'
        'o = o  0\n'
        'n = n  0')

def test_intention_intention():
    """ Test levenshtein('intention', 'intention') i.e. identity """
    result = ponto.levenshtein('intention', 'intention')
    assert result.matrix[ponto.Coordinates(9, 9)].cumulative_cost == 0
    assert ponto.min_edit_distance(result) == 0
    assert ponto.vertical_alignment(result) == (
        'i = i  0\n'
        'n = n  0\n'
        't = t  0\n'
        'e = e  0\n'
        'n = n  0\n'
        't = t  0\n'
        'i = i  0\n'
        'o = o  0\n'
        'n = n  0')

def test_cat_horse():
    """ Test levenshtein('llach', 'llam')  """
    src = 'llach'
    targ = 'llam'
    result = ponto.levenshtein(src, targ)
    last_cell = result.matrix[ponto.Coordinates(len(targ), len(src))]
    assert last_cell.cumulative_cost == 3
    assert ponto.min_edit_distance(result) == 3
    assert ponto.vertical_alignment(result) == (
        'l = l  0\n'
        'l = l  0\n'
        'a = a  0\n'
        'c >    1\n'
        'h ~ m  2')

def test_dag_doge():
    """ Test levenshtein('dag', 'doge')  """
    src = 'dag'
    targ = 'doge'
    result = ponto.levenshtein(src, targ)
    last_cell = result.matrix[ponto.Coordinates(len(targ), len(src))]
    assert last_cell.cumulative_cost == 3
    assert ponto.min_edit_distance(result) == 3
    assert ponto.vertical_alignment(result) == (
        'd = d  0\n'
        'a ~ o  2\n'
        'g = g  0\n'
        '  < e  1')

def test_list_of_letters():
    """ Test sequence of strings rather than plain oldstrings. """
    src = ['ll', 'a', 'ch']
    targ = ['ll', 'a', 'm']
    result = ponto.levenshtein(src, targ)
    assert ponto.vertical_alignment(result) == (
        'll = ll  0\n'
        'a  = a   0\n'
        'ch ~ m   2')

def test_tuple_of_numbers():
    """ Test comparanda that are tuples of numbers. """
    result = ponto.levenshtein((6, 78, 5), (6, 79, 5))
    assert ponto.vertical_alignment(result) == (
        '6  = 6   0\n'
        '78 ~ 79  2\n'
        '5  = 5   0')

def test_ins_cost_letters():
    """ Change insertion cost to be higher for letters than other symbols. """
    def my_ins_cost(insertion):
        """ 1 for letters, 0.2 for other symbols. """
        return 1 if unicodedata.category(insertion).startswith('L') else 0.2
    result = ponto.levenshtein('cowgirl', 'cow-girls', ins_costs=my_ins_cost)
    assert ponto.min_edit_distance(result) == 1.2
    assert ponto.vertical_alignment(result) == (
        'c = c  0\n'
        'o = o  0\n'
        'w = w  0\n'
        '  < -  0.2\n'
        'g = g  0\n'
        'i = i  0\n'
        'r = r  0\n'
        'l = l  0\n'
        '  < s  1')

def test_delete_circumflex():
    """ Test of special deletion function. """
    def my_del_cost(deletion):
        """ 0.3 for ^ else 1 """
        return 0.3 if deletion == '\N{COMBINING CIRCUMFLEX ACCENT}' else 1
    result = ponto.levenshtein(
        unicodedata.normalize('NFD', 'être'), 'etr', del_costs=my_del_cost)
    assert ponto.min_edit_distance(result) == 1.3
    assert ponto.vertical_alignment(result) == (
        'e = e  0\n'
        '̂ >    0.3\n'
        't = t  0\n'
        'r = r  0\n'
        'e >    1')

def test_sub_fun():
    """ Test of special substitution function. """
    def my_sub_cost(src, targ):
        """ Mismatch is √2 """
        return 0 if src == targ else sqrt(2)
    result = ponto.levenshtein('bard', 'bart', sub_costs=my_sub_cost)
    assert ponto.min_edit_distance(result) == sqrt(2)
    assert ponto.vertical_alignment(result) == (
        'b = b  0\n'
        'a = a  0\n'
        'r = r  0\n'
        'd ~ t  1.4142135623730951')

def test_backtrace():
    """ Test get_one_backtrace. """
    result = ponto.levenshtein('cat', 'coats')
    backtrace = ponto.get_one_backtrace(result)
    assert backtrace[0] == ponto.EditStep(
        source='c', target='c',
        cell=ponto.Cell(
            this_cost=0, cumulative_cost=0, operation=ponto.Operation.SUB))
    assert backtrace[1] == ponto.EditStep(
        source=None, target='o',
        cell=ponto.Cell(
            this_cost=1, cumulative_cost=1, operation=ponto.Operation.INS))
    assert backtrace[2] == ponto.EditStep(
        source='a', target='a',
        cell=ponto.Cell(
            this_cost=0, cumulative_cost=1, operation=ponto.Operation.SUB))

# Local Variables:
# mode: python
# indent-tabs-mode: nil
# tab-width: 4
# coding: utf-8-unix
# End:
