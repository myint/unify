# Copyright (C) 2013 Steven Myint

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""Modifies strings to all use the same quote where possible."""

from __future__ import print_function
from __future__ import unicode_literals

import io
import os
import tokenize


__version__ = '0.1.5'


try:
    unicode
except NameError:
    unicode = str


def format_code(source, preferred_quote="'"):
    """Return source code with quotes unified."""
    try:
        return _format_code(source, preferred_quote)
    except (tokenize.TokenError, IndentationError):
        return source


def _format_code(source, preferred_quote):
    """Return source code with quotes unified."""
    if not source:
        return source

    sio = io.StringIO(source)
    formatted = ''
    previous_line = ''
    last_row = 0
    last_column = -1
    last_non_whitespace_token_type = None
    for token in tokenize.generate_tokens(sio.readline):
        token_type = token[0]
        token_string = token[1]
        start_row, start_column = token[2]
        end_row, end_column = token[3]
        line = token[4]

        # Preserve escaped newlines
        if (
            last_non_whitespace_token_type != tokenize.COMMENT and
            start_row > last_row and
            (previous_line.endswith('\\\n') or
             previous_line.endswith('\\\r\n') or
             previous_line.endswith('\\\r'))
        ):
            formatted += previous_line[len(previous_line.rstrip(' \t\n\r\\')):]

        # Preserve spacing
        if start_row > last_row:
            last_column = 0
        if start_column > last_column:
            formatted += line[last_column:start_column]

        if (token_type == tokenize.STRING):
            formatted += unify_quotes(token_string,
                                      preferred_quote=preferred_quote)
        else:
            formatted += token_string

        previous_line = line

        last_row = end_row
        last_column = end_column

        if token_type not in [tokenize.INDENT, tokenize.NEWLINE, tokenize.NL]:
            last_non_whitespace_token_type = token_type

    return formatted


def unify_quotes(token_string, preferred_quote):
    """Return string with quotes changed to preferred_quote if possible."""
    bad_quote = {'"': "'",
                 "'": '"'}[preferred_quote]

    if not token_string.startswith(bad_quote):
        return token_string

    if token_string.count(bad_quote) != 2:
        return token_string

    if preferred_quote in token_string:
        return token_string

    assert token_string.startswith(bad_quote)
    assert token_string.endswith(bad_quote)
    assert len(token_string) >= 2

    return preferred_quote + token_string[1:-1] + preferred_quote


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


def format_file(filename, args, standard_out):
    """Run format_code() on a file."""
    encoding = detect_encoding(filename)
    with open_with_encoding(filename, encoding=encoding) as input_file:
        source = input_file.read()
        formatted_source = format_code(
            source,
            preferred_quote=args.quote)

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


def main(argv, standard_out, standard_error):
    """Main entry point."""
    import argparse
    parser = argparse.ArgumentParser(description=__doc__, prog='unify')
    parser.add_argument('-i', '--in-place', action='store_true',
                        help='make changes to files instead of printing diffs')
    parser.add_argument('-r', '--recursive', action='store_true',
                        help='drill down directories recursively')
    parser.add_argument('--quote', help='preferred quote', default="'")
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + __version__)
    parser.add_argument('files', nargs='+',
                        help='files to format')

    args = parser.parse_args(argv[1:])

    filenames = list(set(args.files))
    while filenames:
        name = filenames.pop(0)
        if args.recursive and os.path.isdir(name):
            for root, directories, children in os.walk(name):
                filenames += [os.path.join(root, f) for f in children
                              if f.endswith('.py') and
                              not f.startswith('.')]
                directories[:] = [d for d in directories
                                  if not d.startswith('.')]
        else:
            try:
                format_file(name, args=args, standard_out=standard_out)
            except IOError as exception:
                print(unicode(exception), file=standard_error)
