#!/usr/bin/env python

# Copyright (C) 2013-2018 Steven Myint
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Modifies strings to all use the same quote where possible."""

from __future__ import print_function
from __future__ import unicode_literals

from abc import ABCMeta, abstractmethod, abstractproperty
import io
from itertools import chain, count
import os
import re
import signal
import sys
import tokenize

import untokenize


__version__ = '0.5'


try:
    unicode
except NameError:
    unicode = str


class AbstractString:
    """Interface to transform strings."""
    __metaclass__ = ABCMeta

    @abstractmethod
    def reformat(self, rules): pass

    @abstractproperty
    def token(self): pass

    @abstractproperty
    def old_token(self): pass


class ImmutableString(AbstractString):
    """
    Null object.

    Don't transform string.
    """

    def __init__(self, body):
        self.body = body

    def reformat(self, rules): pass

    @property
    def token(self):
        return self.body

    @property
    def old_token(self):
        return self.body


class SimpleString(AbstractString):
    """
    String without quote in body.

    Use prefered_quote rule.
    """

    def __init__(self, prefix, quote, body):
        self.prefix = prefix
        self.quote = quote
        self.body = body
        self.old_prefix = prefix
        self.old_quote = quote

    def reformat(self, rules):
        preferred_quote = rules['preferred_quote']
        self.quote = preferred_quote

    @property
    def token(self):
        return '{prefix}{quote}{body}{quote}'.format(
            prefix=self.prefix, quote=self.quote, body=self.body
        )

    @property
    def old_token(self):
        return '{prefix}{quote}{body}{quote}'.format(
            prefix=self.old_prefix, quote=self.old_quote, body=self.body
        )


class SimpleEscapeString(AbstractString):
    """
    String with one type of quote in body.

    Use escape_simple and preferred_quote rules.
    """
    OPPOSITE_QUOTE = {"'": '"', '"': "'"}

    def __init__(self, prefix, quote, body):
        self.prefix = prefix
        self.quote = quote
        self.body = body
        self.old_prefix = prefix
        self.old_quote = quote
        self.old_body = body

    def reformat(self, rules):
        preferred_quote = rules['preferred_quote']
        escape_simple = rules['escape_simple']
        quote_in_body = "'" if "'" in self.body else '"'

        if escape_simple == 'ignore': return

        body = drop_escape_backslash(self.body)
        if escape_simple == 'opposite':
            self.quote = self.OPPOSITE_QUOTE[quote_in_body]
        else:
            self.quote = preferred_quote
            if preferred_quote == quote_in_body:
                body = body.replace(quote_in_body, '\\' + quote_in_body)
        self.body = body

    @property
    def token(self):
        return '{prefix}{quote}{body}{quote}'.format(
            prefix=self.prefix, quote=self.quote, body=self.body
        )

    @property
    def old_token(self):
        return '{prefix}{quote}{body}{quote}'.format(
            prefix=self.old_prefix, quote=self.old_quote, body=self.old_body
        )


def drop_escape_backslash(body):
    bs_pattern = '(\\\\+[\'"])'
    splitted_body = re.split(bs_pattern, body)

    def _drop_escape_bs(string):
        if string.startswith('\\') and len(string) % 2 == 0:
            string = string[1:]
        return string

    splitted_body = [_drop_escape_bs(chunk) for chunk in splitted_body]
    body = ''.join(splitted_body)
    return body


class SimpleEscapeFstring(AbstractString):
    """
    F-string with one type of quote in body.

    Not fully implemented.
    Use escape_simple and preferred_quote rules.
    """

    def __init__(self, prefix, quote, body, parsed_body, expr_ids):
        self.prefix = prefix
        self.quote = quote
        self.body = body
        self.parsed_body = parsed_body
        self.expr_ids = expr_ids
        self.old_prefix = prefix
        self.old_quote = quote
        self.old_body = body

    def reformat(self, rules):
        # Not implemented yet
        pass

    @property
    def token(self):
        return '{prefix}{quote}{body}{quote}'.format(
            prefix=self.prefix, quote=self.quote, body=self.body
        )

    @property
    def old_token(self):
        return '{prefix}{quote}{body}{quote}'.format(
            prefix=self.old_prefix, quote=self.old_quote, body=self.old_body
        )


class FstringParser:
    """Parse f-string to text and expression parts."""

    def __init__(self, body):
        self.body = body
        self.parsed_body = None
        self.expr_area_idx = None
        self.texts = None
        self.expressions = None
        self.expression_ids = None

    def parse(self):
        expr_areas = self.find_expression_areas()
        self._parse(expr_areas)
        self._indexfy_parsed_body()

    def _parse(self, expr_areas):
        if not expr_areas:
            self.parsed_body = [self.body]
            return

        parsed_body = []
        if expr_areas[0][0] != 0:
            parsed_body.append(self.body[:expr_areas[0][0]])

        next_areas = chain(expr_areas, [(len(self.body), None)])
        next(next_areas)
        for (cur_start, cur_end), (next_start, _) in zip(expr_areas, next_areas):
            chunk = self.body[cur_start:cur_end]
            parsed_body.append(chunk)
            if cur_end != next_start:
                chunk = self.body[cur_end:next_start]
                parsed_body.append(chunk)
        self.parsed_body = parsed_body

    def find_expression_areas(self):
        """
        Work like state machine.

        Has two states: outside expression area and inside it.
        If outside it looks for opening brace, ensure that this is not escape brace and
        switch to inside mode.
        If inside it counts braces to search close pair. If found switch to outside mode.
        Return list of numbers for slice.
        """
        expression_area = []
        expr_area_mode = False
        escape_mark = False
        brace_count = 0
        next_chars = chain(self.body, [None])
        next(next_chars)
        start_expr_area = None
        for pos, cur_char, next_char in zip(count(), self.body, next_chars):
            if not expr_area_mode:
                if escape_mark:
                    escape_mark = False
                    continue
                if cur_char == '{' and next_char == '{':
                    escape_mark = True
                    continue
                if cur_char == '{':
                    expr_area_mode = True
                    start_expr_area = pos
                    brace_count += 1
            else:
                if cur_char == '{':
                    brace_count += 1
                if cur_char == '}':
                    brace_count -= 1
                if cur_char == '}' and brace_count == 0:
                    end_expr_area = pos + 1
                    expression_area.append((start_expr_area,end_expr_area))
                    expr_area_mode = False
        return expression_area

    def _indexfy_parsed_body(self):
        re_expr = re.compile(r'{[^{].*[^}]}|{.}')
        texts = []
        expressions = []
        expression_ids = []
        for i, chunk in enumerate(self.parsed_body):
            if re_expr.match(chunk):
                expressions.append(chunk)
                expression_ids.append(i)
            else:
                texts.append(chunk)
        self.texts = texts
        self.expressions = expressions
        self.expression_ids = expression_ids

    def text_has_single_quote(self):
        return any("'" in tx for tx in self.texts)

    def text_has_double_quote(self):
        return any('"' in tx for tx in self.texts)

    def expression_has_single_quote(self):
        return any("'" in expr for expr in self.expressions)

    def expression_has_double_quote(self):
        return any('"' in expr for expr in self.expressions)


def format_code(source, rules):
    """Return source code with quotes unified."""
    try:
        return _format_code(source, rules)
    except (tokenize.TokenError, IndentationError):
        return source


def _format_code(source, rules):
    """Return source code with quotes unified."""
    if not source:
        return source

    modified_tokens = []

    sio = io.StringIO(source)
    for (token_type,
         token_string,
         start,
         end,
         line) in tokenize.generate_tokens(sio.readline):

        editable_string = get_editable_string(token_type, token_string)
        editable_string.reformat(rules)
        token_string = editable_string.token

        modified_tokens.append((token_type, token_string, start, end, line))

    return untokenize.untokenize(modified_tokens)


def get_editable_string(token_type, token_string):
    """dispatcher function."""
    if token_type != tokenize.STRING:
        return ImmutableString(token_string)

    string_pattern = r'''(?P<prefix>[rubf]*)(?P<quote>['"]{3}|['"])(?P<body>.*)(?P=quote)'''
    m = re.match(string_pattern, token_string, re.I | re.S)

    if not m:
        return ImmutableString(token_string)

    parsed_string = m.groupdict()

    if parsed_string['quote'] in ('"""', "'''"):
        return ImmutableString(token_string)
    if all(qt not in parsed_string['body'] for qt in ("'", '"')):
        return SimpleString(**parsed_string)
    if 'r' in parsed_string['prefix'].lower():
        # don't transform raw string since can't use backslash
        # as escape char
        return ImmutableString(token_string)
    if 'f' in parsed_string['prefix'].lower():
        parser = FstringParser(parsed_string['body'])
        parser.parse()
        text_has_single = parser.text_has_single_quote()
        text_has_double = parser.text_has_double_quote()
        expression_has_single = parser.expression_has_single_quote()
        expression_has_double = parser.expression_has_double_quote()

        if text_has_single and text_has_double:
            # don't transform complicated escape yet
            return ImmutableString(token_string)
        if text_has_single or text_has_double:
            if not expression_has_single and expression_has_double:
                # treat this case as simple string
                return SimpleEscapeString(**parsed_string)
            return SimpleEscapeFstring(
                **parsed_string,
                parsed_body=parser.parsed_body,
                expr_ids=parser.expression_ids
            )
    if all(qt in parsed_string['body'] for qt in ("'", '"')):
        # don't transform complicated escape yet
        return ImmutableString(token_string)
    if any(qt in parsed_string['body'] for qt in ("'", '"')):
        return SimpleEscapeString(**parsed_string)
    return ImmutableString(token_string)


def open_with_encoding(filename, encoding, mode='r'):
    """Return opened file with a specific encoding."""
    return io.open(filename, mode=mode, encoding=encoding,
                   newline='')  # Preserve line endings


def detect_encoding(filename):
    """Return file encoding."""
    try:
        with open(filename, 'rb') as input_file:
            from lib2to3.pgen2 import tokenize as lib2to3_tokenize
            encoding = lib2to3_tokenize.detect_encoding(input_file.readline)[0]

            # Check for correctness of encoding.
            with open_with_encoding(filename, encoding) as input_file:
                input_file.read()

        return encoding
    except (SyntaxError, LookupError, UnicodeDecodeError):
        return 'latin-1'


def format_file(filename, args, standard_out, rules):
    """Run format_code() on a file.

    Returns `True` if any changes are needed and they are not being done
    in-place.

    """
    encoding = detect_encoding(filename)
    with open_with_encoding(filename, encoding=encoding) as input_file:
        source = input_file.read()
        formatted_source = format_code(source, rules)

    if source != formatted_source:
        if args.in_place:
            with open_with_encoding(filename, mode='w',
                                    encoding=encoding) as output_file:
                output_file.write(formatted_source)
        else:
            import difflib
            diff = difflib.unified_diff(
                source.splitlines(),
                formatted_source.splitlines(),
                'before/' + filename,
                'after/' + filename,
                lineterm='')
            standard_out.write('\n'.join(list(diff) + ['']))

            return True

    return False


def _main(argv, standard_out, standard_error):
    """Run quotes unifying on files.

    Returns `1` if any quoting changes are still needed, otherwise
    `None`.

    """
    import argparse
    parser = argparse.ArgumentParser(description=__doc__, prog='unify')
    parser.add_argument('-i', '--in-place', action='store_true',
                        help='make changes to files instead of printing diffs')
    parser.add_argument('-c', '--check-only', action='store_true',
                        help='exit with a status code of 1 if any changes are'
                             ' still needed')
    parser.add_argument('-r', '--recursive', action='store_true',
                        help='drill down directories recursively')
    parser.add_argument('--quote', help='preferred quote', choices=["'", '"'],
                        default="'")
    parser.add_argument('--escape-simple',
                        help='escape strategy if string has one type of quote',
                        choices=['opposite', 'backslash', 'ignore'],
                        default='opposite')
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + __version__)
    parser.add_argument('files', nargs='+',
                        help='files to format')

    args = parser.parse_args(argv[1:])

    rules = {
        'preferred_quote': args.quote,
        'escape_simple': args.escape_simple,
    }
    filenames = list(set(args.files))
    changes_needed = False
    failure = False
    while filenames:
        name = filenames.pop(0)
        if args.recursive and os.path.isdir(name):
            for root, directories, children in os.walk(unicode(name)):
                filenames += [
                    os.path.join(root, f) for f in children
                    if f.endswith('.py') and not f.startswith('.')
                ]

                directories[:] = [
                    d for d in directories if not d.startswith('.')
                ]
        else:
            try:
                if format_file(name, args=args, standard_out=standard_out, rules=rules):
                    changes_needed = True
            except IOError as exception:
                print(unicode(exception), file=standard_error)
                failure = True

    if failure or (args.check_only and changes_needed):
        return 1


def main():  # pragma: no cover
    """Return exit status."""
    try:
        # Exit on broken pipe.
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except AttributeError:
        # SIGPIPE is not available on Windows.
        pass

    try:
        return _main(sys.argv,
                     standard_out=sys.stdout,
                     standard_error=sys.stderr)
    except KeyboardInterrupt:
        return 2


if __name__ == '__main__':
    sys.exit(main())  # pragma: no cover
