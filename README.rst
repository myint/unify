unify
=====

Modifies strings to all use the same quote where possible.

Example
-------

After running::

    $ umify example.py

this code

.. code-block:: python

    x = "abc"
    y = 'hello'

gets formatted into this

.. code-block:: python

    x = 'abc'
    y = 'hello'
