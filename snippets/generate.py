#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import argparse
import os
import os.path
import ansible.modules
from ansible.utils import plugin_docs


def get_documents():
    for root, dirs, files in os.walk(os.path.dirname(ansible.modules.__file__)):
        for f in files:
            if f == '__init__.py' or not f.endswith('py') or f.startswith('_'):
                continue
            documentation = plugin_docs.get_docstring(os.path.join(root, f))[0]
            if documentation is None:
                continue
            yield documentation

def to_snippet(document):
    snippet = []
    if 'options' in document:
        if args.sort:
            options = sorted(document['options'].items(), key=lambda x: x[1].get('required') or x[0])
        else:
            options = sorted(document['options'].items(), key=lambda x: x[1].get('required'), reverse=True)

        for index, (name, option) in enumerate(options, 1):
            if 'choices' in option:
                value = '|'.join('%s' % choice for choice in option['choices'])
                value = '#' + value if len(option['choices']) != 0 else ''
            elif option.get('default') is not None and option['default'] != 'None':
                value = option['default']
                if isinstance(value, bool):
                    value = 'yes' if value else 'no'
            else:
                value = ''

            if args.style == 'dictionary':
                delim = ': '
            else:
                delim = '='

            if name == 'free_form':  # special for command/shell
                snippet.append('\t\t${%d:%s%s%s}' % (index, name, delim, value))
            elif isinstance(value, unicode) and len(value) == 0:
                snippet.append('\t\t%s%s${%d}' % (name, delim, index))
            else:
                snippet.append('\t\t%s%s${%d:%s}' % (name, delim, index, value))

        # insert a line to seperate required/non-required field
        for index, (_, option) in enumerate(options):
            if option.get("required", False) is False:
                if index != 0:
                    snippet.insert(index, '')
                break

    if args.style == 'dictionary':
        snippet.insert(0, '\t%s:' % (document['module']))
    else:
        snippet.insert(0, '\t%s:%s' % (document['module'], ' >' if len(snippet) else ''))
    snippet.insert(0, 'snippet %s' % (document['module']))
    snippet.append('')
    return "\n".join(snippet)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--output',
        help='output filename',
        default='ansible.snippets'
    )
    parser.add_argument(
        '--style',
        help='yaml format to use for snippets',
        choices=['multiline', 'dictionary'],
        default='multiline'
    )
    parser.add_argument(
        '--sort',
        help='sort module arguments',
        action='store_true',
        default=False
    )

    args = parser.parse_args()

    with open(args.output, "w") as f:
        f.writelines(["# THIS FILE IS AUTOMATED GENERATED, PLEASE DON'T MODIFY BY HAND\n", "\n"])
        for document in get_documents():
            if 'deprecated' in document:
                continue
            f.write(to_snippet(document).encode('utf-8'))
            f.write("\n\n")
