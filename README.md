

**Note:** This is an alpha pre-release.  To install, use:

    pip install git+https://github.com/tomduck/pandoc-theoremnos.git --user

(to upgrade append the `--upgrade` flag).


pandoc-theoremnos 2.0.0a3
=========================

*pandoc-theoremnos* is a [pandoc] filter for numbering theorem-like environments and their references when converting markdown to other formats.  It is part of the [pandoc-xnos] filter suite.  LaTeX/pdf, html, and epub output have native support.  Native support for docx output is a work in progress.

Demonstration: Processing [demo.md] with pandoc + pandoc-theoremnos gives numbered theorems and references in [pdf], [tex], [html], [epub] and other formats.

[pandoc-eqnos Issue #18]: https://github.com/tomduck/pandoc-eqnos/issues/18
[demo.md]: https://raw.githubusercontent.com/tomduck/pandoc-theoremnos/master/demos/demo.md
[pdf]: https://raw.githack.com/tomduck/pandoc-theoremnos/demos/demo.pdf
[tex]: https://raw.githack.com/tomduck/pandoc-theoremnos/demos/demo.tex
[html]: https://raw.githack.com/tomduck/pandoc-theoremnos/demos/demo.html
[epub]: https://raw.githack.com/tomduck/pandoc-theoremnos/demos/demo.epub

This version of pandoc-theoremnos was tested using pandoc 1.15.2 - 2.7.3,<sup>[1](#footnote1)</sup> and may be used with linux, macOS, and Windows.  Bug reports and feature requests may be posted on the project's [Issues tracker].  If you find pandoc-theoremnos useful, then please kindly give it a star [on GitHub].

See also: [pandoc-fignos], [pandoc-eqnos], [pandoc-secnos], [pandoc-tablenos] \
Other filters: [pandoc-comments], [pandoc-latex-extensions]

[pandoc]: http://pandoc.org/
[pandoc-xnos]: https://github.com/tomduck/pandoc-xnos
[Issues tracker]: https://github.com/tomduck/pandoc-theoremnos/issues
[on GitHub]: https://github.com/tomduck/pandoc-theoremnos
[pandoc-fignos]: https://github.com/tomduck/pandoc-fignos
[pandoc-eqnos]: https://github.com/tomduck/pandoc-eqnos
[pandoc-secnos]: https://github.com/tomduck/pandoc-secnos
[pandoc-tablenos]: https://github.com/tomduck/pandoc-tablenos
[pandoc-comments]: https://github.com/tomduck/pandoc-comments
[pandoc-latex-extensions]: https://github.com/tomduck/pandoc-latex-extensions


Contents
--------

 1. [Installation](#installation)
 2. [Usage](#usage)
 3. [Markdown Syntax](#markdown-syntax)
 4. [Customization](#customization)
 5. [Technical Details](#technical-details)
 6. [Getting Help](#getting-help)
 7. [Development](#development)
 8. [What's New](#whats-new)


Installation
------------

Pandoc-theoremnos requires [python], a programming language that comes pre-installed on macOS and linux.  It is easily installed on Windows -- see [here](https://realpython.com/installing-python/).  Either python 2.7 or 3.x will do.

Pandoc-theoremnos may be installed using the shell command

    pip install pandoc-theoremnos --user

and upgraded by appending `--upgrade` to the above command.  Pip is a program that downloads and installs software from the Python Package Index, [PyPI].  It normally comes installed with a python distribution.<sup>[2](#footnote2)</sup>

__Pandoc-theoremnos has not (yet) been packaged for pip, please install from source.__

Instructions for installing from source are given in [DEVELOPERS.md].

[python]: https://www.python.org/
[PyPI]: https://pypi.python.org/pypi
[DEVELOPERS.md]: DEVELOPERS.md


Usage
-----

Pandoc-theoremnos is activated by using the

    --filter pandoc-theoremnos

option with pandoc.  Alternatively, use

    --filter pandoc-xnos

to activate all of the filters in the [pandoc-xnos] suite (if installed).

Any use of `--filter pandoc-citeproc` or `--bibliography=FILE` should come *after* the `pandoc-theoremnos` or `pandoc-xnos` filter calls.


Markdown Syntax
---------------

The cross-referencing syntax used by pandoc-theoremnos was worked out in [pandoc-eqnos Issue #18].
As there is no particular theorem markup in markdown, definition lists are used instead.

To mark a definition list as a theorem, definition, lemma, proof, etc., add an id to its attributes:

    [My Theorem]{#thm:id}
    : This is my theorem.

A prefix such as `#thm:` is required and specifies the type. Types must be defined by [customization](#customization) before being usable. `id` should be replaced with a unique identifier composed of letters, numbers, dashes and underscores.  The term `My Theorem` is the optional name of the theorem.

To reference the theorem, use

    @thm:id

or

    {@thm:id}

Curly braces protect a reference and are stripped from the output.


### Clever References ###

Writing markdown like

    See Theorem @thm:id.

seems a bit redundant.  Pandoc-theoremnos supports "clever references" via single-character modifiers in front of a reference.  Users may write

     See +@thm:id.

to have the reference name (i.e., "Theorem") automatically generated.  The above form is used mid-sentence.  At the beginning of a sentence, use

     *@thm:id

instead.  If clever references are enabled by default (see [Customization](#customization), below), then users may disable it for a given reference using<sup>[2](#footnote2)</sup>

    !@thm:id

Note: When using `*thm:id` and emphasis (e.g., `*italics*`) in the same sentence, the `*` in the clever reference must be backslash-escaped; e.g., `\*thm:id`.


### Disabling Links ###

To disable a link on a reference, set `nolink=True` in the reference's attributes:

    @thm:id{nolink=True}


Customization
-------------

Pandoc-theoremnos may be customized by setting variables in the [metadata block] or on the command line (using `-M KEY=VAL`).  The following variables are supported:

  * `theoremnos-names` - This is mandatory and specifies the list of
    theorem-like environments. Every list entry is a map with two entries:
    `id` specifies the type identifier (e.g. thm) whereas `name` sets
    the printed name that will be put in front of the number (e.g. Theorem).

  * `theoremnos-warning-level` or `xnos-warning-level` - Set to `0` for
    no warnings, `1` for critical warnings, or `2` (default) for
    all warnings.  Warning level 2 should be used when
    troubleshooting.

  * `theoremnos-cleveref` or just `cleveref` - Set to `True` to assume
    "+" clever references by default;

  * `xnos-capitalise` - Capitalises the names of "+" references
    (e.g., change from "table" to "Table");

  * `theoremnos-number-by-section` or `xnos-number-by-section` - Set to
    `True` to number theorems by section (i.e. Theorem 1.1, 1.2, etc in
    Section 1, and Theorem 2.1, 2.2, etc in Section 2).  For LaTeX/pdf,
    html, and epub output, this feature should be used together with
    pandoc's `--number-sections`
    [option](https://pandoc.org/MANUAL.html#option--number-sections)
    enabled.  For docx, use [docx custom styles] instead.

    This option should not be set for numbering by chapter in
    LaTeX/pdf book document classes.

  * `xnos-number-offset` - Set to an integer to offset the section
    numbers when numbering tables by section.  For html and epub
    output, this feature should be used together with pandoc's
    `--number-offset`
    [option](https://pandoc.org/MANUAL.html#option--number-sections)
    set to the same integer value.  For LaTeX/PDF, this option
    offsets the actual section numbers as required.

  * `theoremnos-shared-counter` - Set to 'True' if all theorem
    type shall share the same counter (i.e. Definition 1, Theorem 2)
    instead of counting separately for every type.

Note that variables beginning with `theoremnos-` apply to only pandoc-theoremnos, whereas variables beginning with `xnos-` apply to all of the pandoc-fignos/eqnos/tablenos/secnos/theremnos.

[metadata block]: http://pandoc.org/README.html#extension-yaml_metadata_block
[docx custom styles]: https://pandoc.org/MANUAL.html#custom-styles


Technical Details
-----------------

### TeX/pdf Output ###

During processing, pandoc-theoremnos inserts packages and supporting TeX into the `header-includes` metadata field.  To see what is inserted, set the `theoremnos-warning-level` meta variable to `2`.  Note that any use of pandoc's `--include-in-header` option [overrides](https://github.com/jgm/pandoc/issues/3139) all `header-includes`.

An example reference in TeX looks like

~~~latex
See \cref{thm:1}.
~~~

For every entry in the `theoremnos-names` meta variable, a theorem type will be defined like

~~~latex
\newtheorem{thm}{Theorem}
~~~

An example theorem looks like

~~~latex
\begin{thm}[My Theorem]
  \label{th:1}
  This is my theorem.
\end{thm}
~~~

Other details:

  * The `cleveref` and `caption` packages are used for clever
    references and caption control, respectively; 
  * The `\label` and `\ref` macros are used for table labels and
    references, respectively (`\Cref` and `\cref` are used for
    clever references);
  * Clever reference names are set with `\Crefname` and `\crefname`;


### Other Output Formats ###

An example reference in html looks like

~~~html
See theorem <a href="#thm:1">1</a>.
~~~

An example theorem looks like

~~~html
<dl id="thm:1" class="theoremnos">
  <dt>Theorem 1 (My Theorem):</dt>
  <dd>
     This is my theorem.
  </dd>
</dl>
~~~


### Docx Output ###

Docx OOXML output is under development and subject to change.  Native capabilities will be used wherever possible.


Getting Help
------------

If you have any difficulties with pandoc-theoremnos, or would like to see a new feature, then please submit a report to our [Issues tracker].


Development
-----------

Pandoc-theoremnos will continue to support pandoc 1.15-onward and python 2 & 3 for the foreseeable future.  The reasons for this are that a) some users cannot upgrade pandoc and/or python; and b) supporting all versions tends to make pandoc-theoremnos more robust.

Developer notes are maintained in [DEVELOPERS.md].


What's New
----------

**New in 2.0.0:** Initial release.


----

**Footnotes**

<a name="footnote1">1</a>: Pandoc 2.4 [broke](https://github.com/jgm/pandoc/issues/5099) how references are parsed, and so is not supported.

<a name="footnote2">2</a>: Anaconda users may be tempted to use `conda` instead.  This is not advised.  The packages distributed on the Anaconda cloud are unofficial, are not posted by me, and in some cases are ancient.  Some tips on using `pip` in a `conda` environment may be found [here](https://www.anaconda.com/using-pip-in-a-conda-environment/).

<a name="footnote3">3</a>: The disabling modifier "!" is used instead of "-" because [pandoc unnecessarily drops minus signs] in front of references.

[pandoc unnecessarily drops minus signs]: https://github.com/jgm/pandoc/issues/2901
