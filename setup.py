"""setup.py - install script for pandoc-theoremnos."""

# Copyright 2015-2019 Thomas J. Duck, Johannes Schlatow.
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

import re
import io

from setuptools import setup

DESCRIPTION = """\
A pandoc filter for numbering tables and their references
when converting markdown to other formats.
"""

# From https://stackoverflow.com/a/39671214
__version__ = re.search(
    r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
    io.open('pandoc_theoremnos.py', encoding='utf_8_sig').read()
    ).group(1)

setup(
    name='pandoc-theoremnos',
    version=__version__,

    author='Thomas J. Duck',
    author_email='tomduck@tomduck.ca',
    description='Theorem number filter for pandoc',
    long_description=DESCRIPTION,
    license='GPL',
    keywords='pandoc table numbers filter',
    url='https://github.com/tomduck/pandoc-theoremnos',
    download_url='https://github.com/tomduck/pandoc-theoremnos/tarball/' + \
                 __version__,

    install_requires=['pandoc-xnos~=2.5.0, < 3.0'],

    py_modules=['pandoc_theoremnos'],
    entry_points={'console_scripts':['pandoc-theoremnos = pandoc_theoremnos:main']},

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: End Users/Desktop',
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python'
        ],
)
