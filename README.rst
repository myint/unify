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

    a = "abc"
    b = 'hello'
    c = 'this \' is quote'
    d = 'this " is another quote'

gets formatted into this

.. code-block:: python

    a = 'abc'
    b = 'hello'
    c= "this ' is quote"
    d = 'this " is another quote'
