Pontospell
==========

Ponto is a Python program and library for measuring degrees of partial correctness in spelling experiments.
It was developed in the [Reading and Language Lab] at [Washington University in St. Louis] primarily to support research in how children learn the fundamental principles of writing systems.
It focuses on finding and scoring the best interpretation of a spelling as an attempt to represent the phonemes of a word by means of the sound-to-spelling correspondences in an alphabetic orthography.

  [Reading and Language Lab]: http://pages.wustl.edu/readingandlanguagelab "RLL home page"
  [Washington University in St. Louis]: http://wustl.edu/ "WUStL home page"

We are in the initial steps of uploading our software to GitHub.
In the interim, a core version of the Ponto software can be downloaded from http://spell.psychology.wustl.edu/, where it may also be accessed as a Web service.

So far we have uploaded a core component for aligning sequences by minimizing string edit distance:

``` python
>>> import pontospell.align as ponto
>>> result = ponto.levenshtein('intention', 'execution')
>>> ponto.min_edit_distance(result)
8
>>> print(ponto.vertical_alignment(result))
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
```

The function operates on any type of sequence.
This flexibility comes in handy for languages in which certain combinations of characters are treated as if separate letters, such as ‹ll› or ‹dd› in Welsh.
Thus omitting ‹dd› from a spelling would be considered an omission of a single letter.

``` python
>>> result = ponto.levenshtein(['ll', 'a', 'dd'], ['ll', 'a'])
>>> print(ponto.vertical_alignment(result))
ll = ll  0
a  = a   0
dd >     1
```

The default configuration uses Levenshtein’s original operation costs.
You can also pass in functions that define other scores for insertions (intrusive letters), deletions (omissions of required letters), and substitutions.
These functions can be parameterized for different characters.
For example, you could treat omitting diacritics and punctuation as less important than omitting letters.

Licence
-------

Pontospell is distributed under an [MIT licence].

  [MIT licence]: ./LICENSE

Contact
-------

[Brett Kessler]

  [Brett Kessler]: http://spell.psychology.wustl.edu/bkessler.html




