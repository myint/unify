#!/usr/bin/env python

"""Test suite for unify."""

import contextlib
import io
import tempfile

try:
    # Python 2.6
    import unittest2 as unittest
except ImportError:
    import unittest

import unify


try:
    unicode
except NameError:
    unicode = str


class TestUnits(unittest.TestCase):

    def test_detect_encoding_with_bad_encoding(self):
        with temporary_file('# -*- coding: blah -*-\n') as filename:
            self.assertEqual('latin-1',
                             unify.detect_encoding(filename))


class TestSystem(unittest.TestCase):

    def test_diff(self):
        with temporary_file('''\
if True:
    x = "abc"
''') as filename:
            output_file = io.StringIO()
            unify.main(argv=['my_fake_program', filename],
                       standard_out=output_file,
                       standard_error=None)
            self.assertEqual(unicode('''\
@@ -1,2 +1,2 @@
 if True:
-    x = "abc"
+    x = 'abc'
'''), '\n'.join(output_file.getvalue().split('\n')[2:]))


@contextlib.contextmanager
def temporary_file(contents, directory='.', prefix=''):
    """Write contents to temporary file and yield it."""
    f = tempfile.NamedTemporaryFile(suffix='.py', prefix=prefix,
                                    delete=False, dir=directory)
    try:
        f.write(contents.encode('utf8'))
        f.close()
        yield f.name
    finally:
        import os
        os.remove(f.name)


@contextlib.contextmanager
def temporary_directory(directory='.', prefix=''):
    """Create temporary directory and yield its path."""
    temp_directory = tempfile.mkdtemp(prefix=prefix, dir=directory)
    try:
        yield temp_directory
    finally:
        import shutil
        shutil.rmtree(temp_directory)


if __name__ == '__main__':
    unittest.main()
