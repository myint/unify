=====
unify
=====

.. image:: https://travis-ci.org/myint/unify.svg?branch=master
    :target: https://travis-ci.org/myint/unify
    :alt: Build status

Modifies strings to all use the same quote where possible.


Install
=======
::

    $ pip install unify

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

Tip
=======

Run on all python files in Git version control::

    $ unify --in-place $(git ls-files '*.py')
