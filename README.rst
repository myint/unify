=====
unify
=====

.. image:: https://travis-ci.org/myint/unify.svg?branch=master
    :target: https://travis-ci.org/myint/unify
    :alt: Build status

Modifies strings to all use the same quote where possible.


Example
=======

After running::

    $ unify --in-place example.py

this code

.. code-block:: python

    x = "abc"
    y = 'hello'

gets formatted into this

.. code-block:: python

    x = 'abc'
    y = 'hello'

STDIN can be formatted by passing `-` as a filename. The formatted text can be
printed to STDOUT by passing `-s` or `--stdout`.
