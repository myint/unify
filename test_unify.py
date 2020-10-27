#!/usr/bin/env python

"""Test suite for unify."""

from __future__ import unicode_literals

import contextlib
import io
import tempfile
from textwrap import dedent

try:
    # Python 2.6
    import unittest2 as unittest
except ImportError:
    import unittest

import unify


class TestUnitsSimpleString(unittest.TestCase):

    def test_preferred_single(self):
        unify.rules['preferred_quote'] = "'"

        result = unify.format_code('"foo"')
        self.assertEqual(result, "'foo'")

        result = unify.format_code('f"foo"')
        self.assertEqual(result, "f'foo'")

        result = unify.format_code('r"foo"')
        self.assertEqual(result, "r'foo'")

        result = unify.format_code('u"foo"')
        self.assertEqual(result, "u'foo'")

        result = unify.format_code('b"foo"')
        self.assertEqual(result, "b'foo'")

    def test_preferred_double(self):
        unify.rules['preferred_quote'] = '"'

        result = unify.format_code("'foo'")
        self.assertEqual(result, '"foo"')

        result = unify.format_code("f'foo'")
        self.assertEqual(result, 'f"foo"')

        result = unify.format_code("r'foo'")
        self.assertEqual(result, 'r"foo"')

        result = unify.format_code("u'foo'")
        self.assertEqual(result, 'u"foo"')

        result = unify.format_code("b'foo'")
        self.assertEqual(result, 'b"foo"')

    def test_keep_single(self):
        unify.rules['preferred_quote'] = "'"
        result = unify.format_code("'foo'")
        self.assertEqual(result, "'foo'")

    def test_keep_double(self):
        unify.rules['preferred_quote'] = '"'
        result = unify.format_code('"foo"')
        self.assertEqual(result, '"foo"')


class TestUnitsSimpleQuotedString(unittest.TestCase):

    def test_opposite(self):
        unify.rules['preferred_quote'] = "'"
        unify.rules['escape_simple'] = 'opposite'

        result = unify.format_code('''"foo's"''')
        self.assertEqual(result, '''"foo's"''')

        result = unify.format_code("""'foo"s'""")
        self.assertEqual(result, """'foo"s'""")

        result = unify.format_code('''"foo\\"s"''')
        self.assertEqual(result, """'foo"s'""")

        result = unify.format_code("""'foo\\'s'""")
        self.assertEqual(result, '''"foo's"''')

    def test_backslash(self):
        unify.rules['preferred_quote'] = "'"
        unify.rules['escape_simple'] = 'backslash'

        result = unify.format_code('''"foo's"''')
        self.assertEqual(result, """'foo\\'s'""")

        result = unify.format_code("""'foo"s'""")
        self.assertEqual(result, """'foo"s'""")

        result = unify.format_code('''"foo\\"s"''')
        self.assertEqual(result, """'foo"s'""")

        result = unify.format_code("""'foo\\'s'""")
        self.assertEqual(result, """'foo\\'s'""")

    def test_keep_unformatted(self):
        unify.rules['preferred_quote'] = "'"
        unify.rules['escape_simple'] = 'opposite'

        result = unify.format_code('''f"foo's{some_var}"''')
        self.assertEqual(result, '''f"foo's{some_var}"''')

        result = unify.format_code("""r'foo\\'s'""")
        self.assertEqual(result, """r'foo\\'s'""")

    def test_backslash_train(self):
        unify.rules['preferred_quote'] = "'"
        unify.rules['escape_simple'] = 'opposite'

        result = unify.format_code('''"a'b\\'c\\\\'d\\\\\\'e\\\\\\\\'f"''')
        self.assertEqual(result, '''"a'b'c\\\\'d\\\\'e\\\\\\\\'f"''')

        result = unify.format_code('''"\\'a"''')
        self.assertEqual(result, '''"'a"''')

        result = unify.format_code('''"\\\\'a"''')
        self.assertEqual(result, '''"\\\\'a"''')


class TestUnitsTripleQuote(unittest.TestCase):

    def test_no_change(self):
        unify.rules['preferred_quote'] = "'"

        result = unify.format_code('''"""foo"""''')
        self.assertEqual(result, '''"""foo"""''')

        result = unify.format_code('''f"""foo"""''')
        self.assertEqual(result, '''f"""foo"""''')

        result = unify.format_code('''r"""\\t"""''')
        self.assertEqual(result, '''r"""\\t"""''')

        result = unify.format_code('''u"""foo"""''')
        self.assertEqual(result, '''u"""foo"""''')

        result = unify.format_code('''b"""foo"""''')
        self.assertEqual(result, '''b"""foo"""''')


class TestUnitsCode(unittest.TestCase):

    def test_detect_encoding_with_bad_encoding(self):
        with temporary_file('# -*- coding: blah -*-\n') as filename:
            self.assertEqual('latin-1', unify.detect_encoding(filename))

    def test_format_code(self):
        unify.rules['preferred_quote'] = "'"

        self.assertEqual("x = 'abc' \\\n'next'\n",
                         unify.format_code('x = "abc" \\\n"next"\n'))

        self.assertEqual("x = f'abc' \\\nf'next'\n",
                         unify.format_code('x = f"abc" \\\nf"next"\n'))

        self.assertEqual("x = u'abc' \\\nu'next'\n",
                         unify.format_code('x = u"abc" \\\nu"next"\n'))

        self.assertEqual("x = b'abc' \\\nb'next'\n",
                         unify.format_code('x = b"abc" \\\nb"next"\n'))

    def test_format_code_with_backslash_in_comment(self):
        unify.rules['preferred_quote'] = "'"

        self.assertEqual("x = 'abc' #\\\n'next'\n",
                         unify.format_code('x = "abc" #\\\n"next"\n'))

        self.assertEqual("x = f'abc' #\\\nf'next'\n",
                         unify.format_code('x = f"abc" #\\\nf"next"\n'))

        self.assertEqual("x = r'abc' #\\\nr'next'\n",
                         unify.format_code('x = r"abc" #\\\nr"next"\n'))

        self.assertEqual("x = r'abc' \\\nr'next'\n",
                         unify.format_code('x = r"abc" \\\nr"next"\n'))

        self.assertEqual("x = u'abc' #\\\nu'next'\n",
                         unify.format_code('x = u"abc" #\\\nu"next"\n'))

        self.assertEqual("x = b'abc' #\\\nb'next'\n",
                         unify.format_code('x = b"abc" #\\\nb"next"\n'))

    def test_format_code_with_syntax_error(self):
        unify.rules['preferred_quote'] = "'"

        self.assertEqual('foo("abc"\n',
                         unify.format_code('foo("abc"\n'))

        self.assertEqual('foo(f"abc"\n',
                         unify.format_code('foo(f"abc"\n'))

        self.assertEqual('foo(r"Tabs \t, new lines \n."\n',
                         unify.format_code('foo(r"Tabs \t, new lines \n."\n'))

        self.assertEqual('foo(u"abc"\n',
                         unify.format_code('foo(u"abc"\n'))

        self.assertEqual('foo(b"abc"\n',
                         unify.format_code('foo(b"abc"\n'))


class TestSystem(unittest.TestCase):

    def test_diff(self):
        with temporary_file(dedent('''\
            if True:
                x = "abc"
        ''')) as filename:
            output_file = io.StringIO()
            self.assertEqual(
                unify._main(argv=['my_fake_program', filename],
                            standard_out=output_file,
                            standard_error=None),
                None)

            self.assertEqual(
                dedent('''\
                    @@ -1,2 +1,2 @@
                     if True:
                    -    x = "abc"
                    +    x = 'abc'
                '''),
                '\n'.join(output_file.getvalue().split('\n')[2:]))

    def test_check_only(self):
        with temporary_file(dedent('''\
            if True:
                x = "abc"
        ''')) as filename:
            output_file = io.StringIO()
            self.assertEqual(
                unify._main(argv=['my_fake_program', '--check-only', filename],
                            standard_out=output_file,
                            standard_error=None),
                1)

            self.assertEqual(
                dedent('''\
                    @@ -1,2 +1,2 @@
                     if True:
                    -    x = "abc"
                    +    x = 'abc'
                '''),
                '\n'.join(output_file.getvalue().split('\n')[2:]))

    def test_diff_with_empty_file(self):
        with temporary_file('') as filename:
            output_file = io.StringIO()
            unify._main(argv=['my_fake_program', filename],
                        standard_out=output_file,
                        standard_error=None)
            self.assertEqual('', output_file.getvalue())

    def test_diff_with_missing_file(self):
        output_file = io.StringIO()
        non_existent_filename = '/non_existent_file_92394492929'

        self.assertEqual(
            1,
            unify._main(
                argv=['my_fake_program', '/non_existent_file_92394492929'],
                standard_out=None,
                standard_error=output_file))

        self.assertIn(non_existent_filename, output_file.getvalue())

    def test_in_place(self):
        with temporary_file(dedent('''\
            if True:
                x = "abc"
        ''')) as filename:
            output_file = io.StringIO()
            self.assertEqual(
                unify._main(argv=['my_fake_program', '--in-place', filename],
                            standard_out=output_file,
                            standard_error=None),
                None)

            with open(filename) as f:
                self.assertEqual(
                    dedent('''\
                        if True:
                            x = 'abc'
                    '''),
                    f.read())

    def test_in_place_precedence_over_check_only(self):
        with temporary_file(dedent('''\
            if True:
                x = "abc"
        ''')) as filename:
            output_file = io.StringIO()
            self.assertEqual(
                unify._main(argv=['my_fake_program',
                                  '--in-place',
                                  '--check-only',
                                  filename],
                            standard_out=output_file,
                            standard_error=None),
                None)

            with open(filename) as f:
                self.assertEqual(
                    dedent('''\
                        if True:
                            x = 'abc'
                    '''),
                    f.read())

    def test_ignore_hidden_directories(self):
        with temporary_directory() as directory:
            with temporary_directory(prefix='.',
                                     directory=directory) as inner_directory:

                with temporary_file(
                        dedent("""\
                            if True:
                                x = "abc"
                        """),
                        directory=inner_directory):

                    output_file = io.StringIO()
                    self.assertEqual(
                        unify._main(argv=['my_fake_program',
                                          '--recursive',
                                          directory],
                                    standard_out=output_file,
                                    standard_error=None),
                        None)

                    self.assertEqual('', output_file.getvalue().strip())


@contextlib.contextmanager
def temporary_file(contents, directory='.', prefix=''):
    """Write contents to temporary file and yield it."""
    f = tempfile.NamedTemporaryFile(suffix='.py', prefix=prefix,
                                    delete=False, dir=directory)
    try:
        f.write(contents.encode())
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
