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
        rules = {'preferred_quote': "'"}

        result = unify.format_code('"foo"', rules)
        self.assertEqual(result, "'foo'")

        result = unify.format_code('f"foo"', rules)
        self.assertEqual(result, "f'foo'")

        result = unify.format_code('r"foo"', rules)
        self.assertEqual(result, "r'foo'")

        result = unify.format_code('u"foo"', rules)
        self.assertEqual(result, "u'foo'")

        result = unify.format_code('b"foo"', rules)
        self.assertEqual(result, "b'foo'")

    def test_preferred_double(self):
        rules = {'preferred_quote': '"'}

        result = unify.format_code("'foo'", rules)
        self.assertEqual(result, '"foo"')

        result = unify.format_code("f'foo'", rules)
        self.assertEqual(result, 'f"foo"')

        result = unify.format_code("r'foo'", rules)
        self.assertEqual(result, 'r"foo"')

        result = unify.format_code("u'foo'", rules)
        self.assertEqual(result, 'u"foo"')

        result = unify.format_code("b'foo'", rules)
        self.assertEqual(result, 'b"foo"')

    def test_keep_single(self):
        rules = {'preferred_quote': "'"}
        result = unify.format_code("'foo'", rules)
        self.assertEqual(result, "'foo'")

    def test_keep_double(self):
        rules = {'preferred_quote':  '"'}
        result = unify.format_code('"foo"', rules)
        self.assertEqual(result, '"foo"')


class TestUnitsSimpleQuotedString(unittest.TestCase):

    def test_opposite(self):
        rules = {
            'preferred_quote': "'",
            'escape_simple': 'opposite',
        }

        result = unify.format_code('''"foo's"''', rules)
        self.assertEqual(result, '''"foo's"''')

        result = unify.format_code("""'foo"s'""", rules)
        self.assertEqual(result, """'foo"s'""")

        result = unify.format_code('''"foo\\"s"''', rules)
        self.assertEqual(result, """'foo"s'""")

        result = unify.format_code("""'foo\\'s'""", rules)
        self.assertEqual(result, '''"foo's"''')

    def test_backslash(self):
        rules = {
            'preferred_quote': "'",
            'escape_simple': 'backslash',
        }

        result = unify.format_code('''"foo's"''', rules)
        self.assertEqual(result, """'foo\\'s'""")

        result = unify.format_code("""'foo"s'""", rules)
        self.assertEqual(result, """'foo"s'""")

        result = unify.format_code('''"foo\\"s"''', rules)
        self.assertEqual(result, """'foo"s'""")

        result = unify.format_code("""'foo\\'s'""", rules)
        self.assertEqual(result, """'foo\\'s'""")

    def test_keep_unformatted(self):
        rules = {
            'preferred_quote': "'",
            'escape_simple': 'opposite',
        }
        result = unify.format_code("""r'foo\\'s'""", rules)
        self.assertEqual(result, """r'foo\\'s'""")

    def test_backslash_train(self):
        rules = {
            'preferred_quote': "'",
            'escape_simple': 'opposite',
        }

        result = unify.format_code('''"a'b\\'c\\\\'d\\\\\\'e\\\\\\\\'f"''',
                                   rules)

        self.assertEqual(result, '''"a'b'c\\\\'d\\\\'e\\\\\\\\'f"''')

        result = unify.format_code('''"\\'a"''', rules)
        self.assertEqual(result, '''"'a"''')

        result = unify.format_code('''"\\\\'a"''', rules)
        self.assertEqual(result, '''"\\\\'a"''')


class TestUnitsSimpleQuotedFstring(unittest.TestCase):

    def test_no_quote_in_expression_area(self):
        # don't add 'f_string_expression_quote' to ensure it's
        # handled by SimpleQuotedString
        rules = {
            'preferred_quote': "'",
            'escape_simple': 'opposite',
        }
        result = unify.format_code('''f"foo's{some_var}"''', rules)
        self.assertEqual(result, '''f"foo's{some_var}"''')

        rules = {
            'preferred_quote': "'",
            'escape_simple': 'backslash',
        }
        result = unify.format_code('''f"foo's{some_var}"''', rules)
        self.assertEqual(result, """f'foo\\'s{some_var}'""")

        rules = {
            'preferred_quote': '"',
            'escape_simple': 'opposite',
        }
        result = unify.format_code('''f"foo's{some_var}"''', rules)
        self.assertEqual(result, '''f"foo's{some_var}"''')

    def test_single_quote_in_expr_area(self):
        rules = {
            'preferred_quote': "'",
            'escape_simple': 'opposite',
            'f_string_expression_quote': 'single',
        }
        result = unify.format_code('''f"foo{some_dict['a']}"''', rules)
        self.assertEqual(result, '''f"foo{some_dict['a']}"''')

        result = unify.format_code('''f"foo's{some_dict['a']}"''', rules)
        self.assertEqual(result, '''f"foo's{some_dict['a']}"''')

        result = unify.format_code("""f'foo "name" {some_dict["a"]}'""", rules)
        self.assertEqual(result, '''f"foo \\"name\\" {some_dict['a']}"''')

    def test_double_quote_in_expr_area(self):
        rules = {
            'preferred_quote': "'",
            'escape_simple': 'opposite',
            'f_string_expression_quote': 'double',
        }
        result = unify.format_code("""f'foo{some_dict["a"]}'""", rules)
        self.assertEqual(result, """f'foo{some_dict["a"]}'""")

        result = unify.format_code("""f'foo "name" {some_dict["a"]}'""", rules)
        self.assertEqual(result, """f'foo "name" {some_dict["a"]}'""")

        result = unify.format_code('''f"foo's{some_dict['a']}"''', rules)
        self.assertEqual(result, """f'foo\\'s{some_dict["a"]}'""")

    def test_depended_opposite(self):
        rules = {
            'preferred_quote': "'",
            'escape_simple': 'opposite',
            'f_string_expression_quote': 'depended',
        }
        result = unify.format_code('''f"foo{some_dict['a']}"''', rules)
        self.assertEqual(result, '''f"foo{some_dict['a']}"''')

        result = unify.format_code("""f'foo{some_dict["a"]}'""", rules)
        self.assertEqual(result, '''f"foo{some_dict['a']}"''')

        result = unify.format_code('''f"foo's{some_dict['a']}"''', rules)
        self.assertEqual(result, '''f"foo's{some_dict['a']}"''')

        result = unify.format_code('''f"foo \\'name\\' {some_dict['a']}"''', rules)
        self.assertEqual(result, '''f"foo 'name' {some_dict['a']}"''')

        result = unify.format_code("""f'foo "name" {some_dict["a"]}'""", rules)
        self.assertEqual(result, """f'foo "name" {some_dict["a"]}'""")

    def test_depended_backskash(self):
        rules = {
            'preferred_quote': "'",
            'escape_simple': 'backslash',
            'f_string_expression_quote': 'depended',
        }
        result = unify.format_code('''f"foo{some_dict['a']}"''', rules)
        self.assertEqual(result, """f'foo{some_dict["a"]}'""")

        result = unify.format_code("""f'foo{some_dict["a"]}'""", rules)
        self.assertEqual(result, """f'foo{some_dict["a"]}'""")

        result = unify.format_code('''f"foo's{some_dict['a']}"''', rules)
        self.assertEqual(result, """f'foo\\'s{some_dict["a"]}'""")

        result = unify.format_code('''f"foo 'name' {some_dict['a']}"''', rules)
        self.assertEqual(result, """f'foo \\'name\\' {some_dict["a"]}'""")

        result = unify.format_code("""f'foo "name" {some_dict["a"]}'""", rules)
        self.assertEqual(result, """f'foo "name" {some_dict["a"]}'""")

    def test_raw_string(self):
        rules = {
            'preferred_quote': "'",
            'escape_simple': 'opposite',
            'f_string_expression_quote': 'depended',
        }
        result = unify.format_code('''rf"foo{some_dict['a']}"''', rules)
        self.assertEqual(result, '''rf"foo{some_dict['a']}"''')

        result = unify.format_code("""rf'foo{some_dict["a"]}'""", rules)
        self.assertEqual(result, '''rf"foo{some_dict['a']}"''')

        rules = {
            'preferred_quote': "'",
            'escape_simple': 'backslash',
            'f_string_expression_quote': 'depended',
        }
        result = unify.format_code('''rf"foo{some_dict['a']}"''', rules)
        self.assertEqual(result, """rf'foo{some_dict["a"]}'""")

        result = unify.format_code("""rf'foo{some_dict["a"]}'""", rules)
        self.assertEqual(result, """rf'foo{some_dict["a"]}'""")


class TestUnitsTripleQuote(unittest.TestCase):

    def test_no_change(self):
        rules = {'preferred_quote': "'"}

        result = unify.format_code('''"""foo"""''', rules)
        self.assertEqual(result, '''"""foo"""''')

        result = unify.format_code('''f"""foo"""''', rules)
        self.assertEqual(result, '''f"""foo"""''')

        result = unify.format_code('''r"""\\t"""''', rules)
        self.assertEqual(result, '''r"""\\t"""''')

        result = unify.format_code('''u"""foo"""''', rules)
        self.assertEqual(result, '''u"""foo"""''')

        result = unify.format_code('''b"""foo"""''', rules)
        self.assertEqual(result, '''b"""foo"""''')


class TestFstringParser(unittest.TestCase):

    def test_find_expression_areas(self):
        cases = [
            ('text', []),
            ('{bcd}', [(0, 5)]),
            ('{{not exp area}}', []),
            ('{{{def}}}', [(2, 7)]),
            ('{b}{e}', [(0, 3),(3, 6)]),
            ('{bcd}}}', [(0, 5)]),
            ('{{{def}', [(2, 7)]),
        ]
        for source, expected in cases:
            with self.subTest(body=source):
                parser = unify.FstringParser(source)
                result = parser.find_expression_areas()
                self.assertEqual(result, expected)

    def test_parse(self):
        cases = [
            ('text', ['text']),
            ('{bcd}', ['{bcd}']),
            ('{{not exp area}}', ['{{not exp area}}']),
            ('{{{def}}}', ['{{', '{def}', '}}']),
            ('{b}{e}', ['{b}', '{e}']),
            ('{bcd}}}', ['{bcd}', '}}']),
            ('{{{def}', ['{{', '{def}']),
            ('{b}d{f}', ['{b}', 'd', '{f}']),
            ('{ {1} }', ['{ {1} }']),
            ('{{1}}', ['{{1}}']),
            ('{ {{1,2}.pop()} }', ['{ {{1,2}.pop()} }']),
        ]
        for source, expected in cases:
            with self.subTest(body=source):
                parser = unify.FstringParser(source)
                parser.parse()
                result = parser.parsed_body
                self.assertEqual(result, expected)

    def test_indexfy(self):
        cases = [
            ('text', ['text'], [], []),
            ('{bcd}', [], ['{bcd}'], [0]),
            ('{{not exp area}}', ['{{not exp area}}'], [], []),
            ('{{{def}}}', ['{{', '}}'], ['{def}'],[1]),
            ('{b}{e}', [], ['{b}', '{e}'], [0, 1]),
            ('{bcd}}}', ['}}'], ['{bcd}'], [0]),
            ('{{{def}', ['{{'], ['{def}'], [1]),
            ('{b}d{f}', ['d'], ['{b}', '{f}'], [0, 2]),
            ('{ {1} }', [], ['{ {1} }'],[0]),
            ('{{1}}', ['{{1}}'], [],[]),
            ('{ {{1,2}.pop()} }', [], ['{ {{1,2}.pop()} }'], [0]),
        ]
        for source, expected_texts, expected_expr, expected_ids in cases:
            with self.subTest(body=source):
                parser = unify.FstringParser(source)
                parser.parse()
                self.assertEqual(parser.texts, expected_texts)
                self.assertEqual(parser.expressions, expected_expr)
                self.assertEqual(parser.expression_ids, expected_ids)


class TestUnitsCode(unittest.TestCase):

    def test_detect_encoding_with_bad_encoding(self):
        with temporary_file('# -*- coding: blah -*-\n') as filename:
            self.assertEqual('latin-1', unify.detect_encoding(filename))

    def test_format_code(self):
        rules = {'preferred_quote': "'"}

        self.assertEqual("x = 'abc' \\\n'next'\n",
                         unify.format_code('x = "abc" \\\n"next"\n', rules))

        self.assertEqual("x = f'abc' \\\nf'next'\n",
                         unify.format_code('x = f"abc" \\\nf"next"\n', rules))

        self.assertEqual("x = u'abc' \\\nu'next'\n",
                         unify.format_code('x = u"abc" \\\nu"next"\n', rules))

        self.assertEqual("x = b'abc' \\\nb'next'\n",
                         unify.format_code('x = b"abc" \\\nb"next"\n', rules))

    def test_format_code_with_backslash_in_comment(self):
        rules = {'preferred_quote': "'"}

        self.assertEqual("x = 'abc' #\\\n'next'\n",
                         unify.format_code('x = "abc" #\\\n"next"\n', rules))

        self.assertEqual("x = f'abc' #\\\nf'next'\n",
                         unify.format_code('x = f"abc" #\\\nf"next"\n', rules))

        self.assertEqual("x = r'abc' #\\\nr'next'\n",
                         unify.format_code('x = r"abc" #\\\nr"next"\n', rules))

        self.assertEqual("x = r'abc' \\\nr'next'\n",
                         unify.format_code('x = r"abc" \\\nr"next"\n', rules))

        self.assertEqual("x = u'abc' #\\\nu'next'\n",
                         unify.format_code('x = u"abc" #\\\nu"next"\n', rules))

        self.assertEqual("x = b'abc' #\\\nb'next'\n",
                         unify.format_code('x = b"abc" #\\\nb"next"\n', rules))

    def test_format_code_with_syntax_error(self):
        rules = {'preferred_quote': "'"}

        self.assertEqual('foo("abc"\n',
                         unify.format_code('foo("abc"\n', rules))

        self.assertEqual('foo(f"abc"\n',
                         unify.format_code('foo(f"abc"\n', rules))

        self.assertEqual('foo(r"Tabs \t, new lines \n."\n',
                         unify.format_code('foo(r"Tabs \t, new lines \n."\n',
                                           rules))

        self.assertEqual('foo(u"abc"\n',
                         unify.format_code('foo(u"abc"\n', rules))

        self.assertEqual('foo(b"abc"\n',
                         unify.format_code('foo(b"abc"\n', rules))


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
