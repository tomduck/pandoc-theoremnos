#! /usr/bin/env python

"""pandoc-theoremnos: a pandoc filter that inserts theorem nos. and refs."""


__version__ = '2.0.0a3'


# Copyright 2015-2020 Thomas J. Duck and Johannes Schlatow
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


# OVERVIEW
#
# The basic idea is to scan the document twice in order to:
#
#   1. Insert text for the theorem number in each theorem.
#      For LaTeX, change to a numbered theorem and use \label{...}
#      instead.  The theorem labels and associated theorem numbers
#      are stored in the global targets tracker.
#
#   2. Replace each reference with an theorem number.  For LaTeX,
#      replace with \ref{...} instead.
#
# This is followed by injecting header code as needed for certain output
# formats.

# pylint: disable=invalid-name

import re
import functools
import argparse
import json
import textwrap
import uuid

from pandocfilters import walk
from pandocfilters import Div, Plain, RawBlock, RawInline, Math, Str, Span, DefinitionList
from pandocfilters import stringify

import pandocxnos
from pandocxnos import PandocAttributes
from pandocxnos import STRTYPES, STDIN, STDOUT, STDERR
from pandocxnos import check_bool, get_meta
from pandocxnos import repair_refs, process_refs_factory, replace_refs_factory
from pandocxnos import attach_attrs_factory
from pandocxnos import insert_secnos_factory, delete_secnos_factory


# Patterns for matching labels and references
LABEL_PATTERN = None

# Meta variables; may be reset elsewhere
cleveref = False    # Flags that clever references should be used
capitalise = False  # Flags that plusname should be capitalised
names = {}          # Stores names and types of theorems
styles = {}         # Stores styles for tcolorbox
warninglevel = 2        # 0 - no warnings; 1 - some warnings; 2 - all warnings
numbersections = False  # Flags that theorems should be numbered by section
secoffset = 0
sharedcounter = False
texbackend = 'amsthm'

# Processing state variables
cursec = None  # Current section
Ntargets = {}  # Number of targets in current section (or document)
targets = {}   # Maps targets labels to [number/tag, theorem secno]

PANDOCVERSION = None


# Actions --------------------------------------------------------------------

# pylint: disable=too-many-branches
def _process_theorem(value, fmt):
    """Processes the theorem.  Returns a dict containing theorem properties."""

    # pylint: disable=global-statement
    global Ntargets  # Global targets counter
    global cursec    # Current section

    # Initialize the return value
    thm = {'is_unreferenceable': False,
           'is_tagged': False}

    # Parse the theorem attributes
    attrs = thm['attrs'] = PandocAttributes(value[0], 'pandoc')

    # Bail out if the label does not conform to expectations
    assert LABEL_PATTERN and LABEL_PATTERN.match(attrs.id)

    # Identify unreferenceable theorems
    if attrs.id[-1] == ':': # Make up a unique description
        attrs.id += str(uuid.uuid4())
        thm['is_unreferenceable'] = True

    counter = attrs.id.split(':')[0]
    if sharedcounter:
        counter = 'shared'

    # Update the current section number
    if attrs['secno'] != cursec:  # The section number changed
        cursec = attrs['secno']   # Update the global section tracker
        for key, nref in Ntargets.items(): # pylint: disable=unused-variable
            Ntargets[key] = 1              # Resets the global target counter

    # Pandoc's --number-sections supports section numbering latex/pdf, html,
    # epub, and docx
    if numbersections:
        # Latex/pdf supports theorems numbers by section natively.  For the
        # other formats we must hard-code in theorem numbers by section as
        # tags.
        if fmt in ['html', 'html5', 'epub', 'epub2', 'epub3', 'docx'] and \
          'tag' not in attrs:
            attrs['tag'] = str(cursec+secoffset) + '.' + \
              str(Ntargets[counter])
            Ntargets[counter] += 1

    # Save reference information
    thm['is_tagged'] = 'tag' in attrs
    if thm['is_tagged']:   # ... then save the tag
        # Remove any surrounding quotes
        if attrs['tag'][0] == '"' and attrs['tag'][-1] == '"':
            attrs['tag'] = attrs['tag'].strip('"')
        elif attrs['tag'][0] == "'" and attrs['tag'][-1] == "'":
            attrs['tag'] = attrs['tag'].strip("'")
        targets[attrs.id] = pandocxnos.Target(attrs['tag'], cursec,
                                              attrs.id in targets)
    else:
        targets[attrs.id] = pandocxnos.Target(Ntargets[counter], cursec,
                                              attrs.id in targets)
        Ntargets[counter] += 1  # Increment the global reference counter

    return thm

# pylint: disable=too-many-locals
def _add_markup(fmt, thm, value):
    """Adds markup to the output."""

    attrs = thm['attrs']
    ret = None

    if fmt in ['latex', 'beamer']:

        # remark: tagged theorems are not (yet) supported

        # Present theorem as a definition list
        env = attrs.id.split(':')[0]

        tmp = value[0][0]['c'][1]
        title = ''

        if texbackend == 'amsthm':
            if len(tmp) >= 1:
                title = '[%s]' % stringify(tmp)
            start = RawInline('tex',
                             r'\begin{%s}%s%s' % \
                             (env, title,
                              '' if thm['is_unreferenceable'] else
                              '\\label{%s}\n' % attrs.id))
            endtags = RawInline('tex', '\n\\end{%s}' % env)
        elif texbackend == 'tcolorbox':
            if len(tmp) >= 1:
                title = '%s' % stringify(tmp)
            start = RawInline('tex',
                             '\\begin{%s}{%s}{%s}\n' % \
                             (env, title,
                              '' if thm['is_unreferenceable'] else
                              r'%s '%attrs.id.split(':')[1]))
            endtags = RawInline('tex', '\n\\end{%s}' % env)

        content = value[1][0]
        content[0]['c'] = [start] + content[0]['c'] + [endtags]
        ret = content

    elif fmt in ('html', 'html5', 'epub', 'epub2', 'epub3'):
        if isinstance(targets[attrs.id].num, int):  # Numbered reference
            num = Str(' %d'%targets[attrs.id].num)
        else:  # Tagged reference
            assert isinstance(targets[attrs.id].num, STRTYPES)
            text = ' ' + targets[attrs.id].num
            if text.startswith('$') and text.endswith('$'):
                math = text.replace(' ', r'\ ')[1:-1]
                num = Math({"t":"InlineMath", "c":[]}, math)
            else:  # Text
                num = Str(text)

        # Present theorem as a definition list
        outer = RawBlock('html',
                         '<dl%sclass="theoremnos">' % \
                         (' ' if thm['is_unreferenceable'] else
                          ' id="%s" '%attrs.id))
        name = names[attrs.id.split(':')[0]]
        head = RawBlock('html', '<dt>')
        endhead = RawBlock('html', '</dt><dd>')
        title = value[0][0]['c'][1]
        if len(title) >= 1:
            title.insert(0, Str(' ('))
            title.insert(0, num)
            title.append(Str(')'))
        else:
            title.append(num)

        title.insert(0, Str('%s' % name))
        title.append(Str(':'))
        content = value[1][0]
        endtags = RawBlock('html', '</dd></dl>')
        ret = [outer, head, Plain(title), endhead] + content + [endtags]

    # To do: define default behaviour

    return ret

def _is_theorem(item):
    """Returns True if item is a theorem; false otherwise."""
    if item[0][0]['t'] != 'Span':
        return False
    attrs = PandocAttributes(item[0][0]['c'][0], 'pandoc')
    return bool(LABEL_PATTERN.match(attrs.id)) if LABEL_PATTERN else False

def process_theorems(key, value, fmt, meta):  # pylint: disable=unused-argument
    """Processes the attributed definition lists."""

    # Process definition lists and add markup
    if key == 'DefinitionList':

        # Split items into groups of regular and numbered items
        itemgroups = []
        tmp = []
        cond = True
        for v in value:
            if _is_theorem(v) == cond:
                tmp.append(v)
            else:
                cond = not cond
                if tmp:
                    itemgroups.append(tmp)
                tmp = [v]
        if tmp:
            itemgroups.append(tmp)

        # Process each group of items
        ret = []
        for items in itemgroups:
            if _is_theorem(items[0]):  # These are numbered items
                markup = []
                for item in items:  # Iterate entries
                    thm = _process_theorem(item[0][0]['c'], fmt)
                    markup = markup + _add_markup(fmt, thm, item)
                ret.append(Div(['', ['theoremnos'], []], markup))
            else:  # These are regular (unnumbered) items
                ret.append(DefinitionList(items))
        return ret

    return None


# TeX blocks -----------------------------------------------------------------

# Section number offset
SECOFFSET_TEX = r"""
%% pandoc-theoremnos: section number offset
\setcounter{section}{%s}
"""


# Main program ---------------------------------------------------------------

# pylint: disable=too-many-statements
def process(meta):
    """Saves metadata fields in global variables and returns a few
    computed fields."""

    # pylint: disable=global-statement
    global cleveref    # Flags that clever references should be used
    global capitalise  # Flags that plusname should be capitalised
    global names       # Sets theorem types and names
    global styles      # Sets styles for tcolorbox
    global warninglevel    # 0 - no warnings; 1 - some; 2 - all
    global LABEL_PATTERN
    global numbersections
    global secoffset
    global sharedcounter
    global texbackend

    # Read in the metadata fields and do some checking

    for name in ['theoremnos-warning-level', 'xnos-warning-level']:
        if name in meta:
            warninglevel = int(get_meta(meta, name))
            pandocxnos.set_warning_level(warninglevel)
            break

    metanames = ['theoremnos-warning-level', 'xnos-warning-level',
                 'theoremnos-cleveref', 'xnos-cleveref',
                 'xnos-capitalise', 'xnos-capitalize',
                 'xnos-caption-separator', # Used by pandoc-fignos/tablenos
                 'theoremnos-names',
                 'xnos-number-by-section',
                 'theoremnos-shared-counter',
                 'theoremnos-number-by-section',
                 'theoremnos-tex-backend',
                 'xnos-number-offset']

    if warninglevel:
        for name in meta:
            if (name.startswith('theoremnos') or name.startswith('xnos')) and \
              name not in metanames:
                msg = textwrap.dedent("""
                          pandoc-theoremnos: unknown meta variable "%s"\n
                      """ % name)
                STDERR.write(msg)

    for name in ['theoremnos-cleveref', 'xnos-cleveref']:
        # 'xnos-cleveref' enables cleveref in all 3 of fignos/eqnos/tablenos
        if name in meta:
            cleveref = check_bool(get_meta(meta, name))
            break

    for name in ['xnos-capitalise', 'xnos-capitalize']:
        # 'xnos-capitalise' enables capitalise in all 4 of
        # fignos/eqnos/tablenos/theoremonos.  Since this uses an option in
        # the caption package, it is not possible to select between the four.
        # 'xnos-capitalize' is an alternative spelling
        if name in meta:
            capitalise = check_bool(get_meta(meta, name))
            break

    for name in ['theoremnos-number-by-section', 'xnos-number-by-section']:
        if name in meta:
            numbersections = check_bool(get_meta(meta, name))
            break

    if 'xnos-number-offset' in meta:
        secoffset = int(get_meta(meta, 'xnos-number-offset'))

    if 'theoremnos-shared-counter' in meta:
        sharedcounter = check_bool(get_meta(meta, 'theoremnos-shared-counter'))

    if 'theoremnos-tex-backend' in meta:
        texbackend = get_meta(meta, 'theoremnos-tex-backend')
        if texbackend != 'amsthm' and texbackend != 'tcolorbox':
            msg = textwrap.dedent("""
                      pandoc-theoremnos: unknown tex-backend "%s"\n
                  """ % texbackend)
            STDERR.write(msg)

    if 'theoremnos-names' in meta:
        assert meta['theoremnos-names']['t'] == 'MetaList'
        for entry in get_meta(meta, 'theoremnos-names'):
            assert isinstance(entry, dict), "%s is of type %s" % \
              (entry, type(entry))
            assert 'id' in entry and isinstance(entry['id'], STRTYPES)
            assert 'name' in entry and isinstance(entry['name'], STRTYPES)
            names[entry['id']] = entry['name']
            if 'style' in entry and isinstance(entry['style'], STRTYPES):
                styles[entry['id']] = entry['style']
            Ntargets[entry['id']] = 0

        Ntargets['shared'] = 0

    if names:
        LABEL_PATTERN = \
          re.compile("(%s):%s" % ('|'.join(names.keys()), r'[\w/-]*'))


def add_tex(meta):
    """Adds tex to the meta data."""

    warnings = warninglevel == 2 and targets and \
      (pandocxnos.cleveref_required() or len(names) or secoffset or \
       numbersections)
    if warnings:
        msg = textwrap.dedent("""\
                  pandoc-theoremnos: Wrote the following blocks to
                  header-includes.  If you use pandoc's
                  --include-in-header option then you will need to
                  manually include these yourself.
              """)
        STDERR.write('\n')
        STDERR.write(textwrap.fill(msg))
        STDERR.write('\n')

    # Update the header-includes metadata.  Pandoc's
    # --include-in-header option will override anything we do here.  This
    # is a known issue and is owing to a design decision in pandoc.
    # See https://github.com/jgm/pandoc/issues/3139.

    if pandocxnos.cleveref_required() and targets:
        tex = """
            %%%% pandoc-theoremnos: required package
            \\usepackage{amsthm}
            \\usepackage%s{cleveref}
        """ % ('[capitalise]' if capitalise else '')
        pandocxnos.add_to_header_includes(
            meta, 'tex', tex,
            regex=r'\\usepackage(\[[\w\s,]*\])?\{cleveref\}')

    if secoffset and targets:
        pandocxnos.add_to_header_includes(
            meta, 'tex', SECOFFSET_TEX % secoffset,
                        regex=r'\\setcounter\{section\}')

    if names:
        tex = """
            %% pandoc-theoremnos: set theorem types
            """
        firstid = None
        for thid, thname in names.items():
            if texbackend == 'amsthm':
                tex += """\\newtheorem{%s}%s{%s}%s
                """ % (thid, '[%s]' % firstid if firstid is not None else '',
                       thname, '[section]' if numbersections and firstid is None \
                       else '')
            elif texbackend == 'tcolorbox':
                style = styles[thid] if thid in styles else ''
                tex += """\\newtcbtheorem[crefname={%s}{%ss},Crefname={%s}{%ss}%s%s]{%s}{%s}{%s}{%s}
            """     % ( thname.lower(), thname.lower(), thname, thname,
                       ',number within=section' if numbersections and firstid is None else '',
                       ',use counter from=%s' % firstid if firstid is not None else '',
                       thid, thname, style, thid)

            if sharedcounter and firstid is None:
                firstid = thid

        pandocxnos.add_to_header_includes(meta, 'tex', tex)

    if warnings:
        STDERR.write('\n')


# pylint: disable=too-many-locals, unused-argument
def main(stdin=STDIN, stdout=STDOUT, stderr=STDERR):
    """Filters the document AST."""

    # pylint: disable=global-statement
    global PANDOCVERSION

    # Read the command-line arguments
    parser = argparse.ArgumentParser(\
      description='Pandoc theorem numbers filter.')
    parser.add_argument(\
      '--version', action='version',
      version='%(prog)s {version}'.format(version=__version__))
    parser.add_argument('fmt')
    parser.add_argument('--pandocversion', help='The pandoc version.')
    args = parser.parse_args()

    # Get the output format and document
    fmt = args.fmt
    doc = json.loads(stdin.read())

    # Initialize pandocxnos
    PANDOCVERSION = pandocxnos.init(args.pandocversion, doc)

    # Chop up the doc
    meta = doc['meta'] if PANDOCVERSION >= '1.18' else doc[0]['unMeta']
    blocks = doc['blocks'] if PANDOCVERSION >= '1.18' else doc[1:]

    # Process the metadata variables
    process(meta)

    if LABEL_PATTERN:
        # First pass
        insert_secnos = insert_secnos_factory(Span)
        delete_secnos = delete_secnos_factory(Span)
        altered = functools.reduce(lambda x, action: walk(x, action, fmt, meta),
                                   [insert_secnos, process_theorems,
                                    delete_secnos], blocks)

        # Second pass
        if fmt in ('latex', 'beamer'):
            process_refs = process_refs_factory(LABEL_PATTERN,
                                                targets.keys())

            STDERR.write('\n')
            STDERR.write(str(LABEL_PATTERN))
            STDERR.write('\n')

            # Latex takes care of inserting the correct plusname/starname
            replace_refs = replace_refs_factory(targets,
                                                cleveref, False,
                                                ['UNUSED'],
                                                ['UNUSED'])
            
            process_all_refs = [process_refs, replace_refs]
        else:
            # Replace each theorem type separately (to insert the correct names)
            process_all_refs = []

            for thid, thname in names.items():
                refs = {}
                for key, value in targets.items():
                    if key.split(':')[0] == thid:
                        refs[key] = value
                if refs:

                    PATTERN = re.compile("%s:%s" % (thid, r'[\w/-]*'))
                    process_refs = process_refs_factory(PATTERN,
                                                        refs.keys())
                    replace_refs = replace_refs_factory(refs,
                                                        cleveref, False,
                                                        [thname],
                                                        [thname])

                    process_all_refs.append(process_refs)
                    process_all_refs.append(replace_refs)

        attach_attrs_span = attach_attrs_factory('pandoc-theoremnos', Span,
                                                 replace=True)
        altered = functools.reduce(lambda x, action: walk(x, action, fmt, meta),
                                   [repair_refs] + process_all_refs +
                                   [attach_attrs_span],
                                   altered)

        if fmt in ['latex', 'beamer']:
            add_tex(meta)

        # Update the doc
        if PANDOCVERSION >= '1.18':
            doc['blocks'] = altered
        else:
            doc = doc[:1] + altered

    # Dump the results
    json.dump(doc, stdout)

    # Flush stdout
    stdout.flush()

if __name__ == '__main__':
    main()
