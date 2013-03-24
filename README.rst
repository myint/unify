unify
=====

.. image:: https://travis-ci.org/myint/unify.png?branch=master
   :target: https://travis-ci.org/myint/unify
   :alt: Build status

Modifies strings to all use the same quote where possible.

Example
-------

After running::

    $ unify example.py

this code

.. code-block:: python

    x = "abc"
    y = 'hello'

gets formatted into this

.. code-block:: python

    x = 'abc'
    y = 'hello'
