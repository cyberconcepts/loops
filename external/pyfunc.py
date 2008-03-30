#
#  Copyright (c) 2008 Helmut Merz helmutm@cy55.de
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

"""
Reading and writing loops objects (represented by IElement objects)
in Python function notation.

$Id$
"""

from zope.cachedescriptors.property import Lazy
from zope.interface import implements

from loops.external.interfaces import IReader, IWriter
from loops.external.element import elementTypes, toplevelElements


class PyReader(object):

    implements(IReader)

    def read(self, input):
        if not isinstance(input, str):
            input = input.read()
        proc = InputProcessor()
        exec input in proc
        return proc.elements


class InputProcessor(dict):

    def __init__(self):
        self.elements = []
        self['__builtins__'] = {}   # security!

    def __getitem__(self, key):
        def factory(*args, **kw):
            element = elementTypes[key](*args, **kw)
            if key in toplevelElements:
                self.elements.append(element)
            return element
        return factory


class PyWriter(object):

    implements(IWriter)

    def write(self, elements, output, level=0):
        for idx, element in enumerate(elements):
            args = []
            for arg in element.posArgs:
                if arg in element:
                    args.append(repr(element[arg]))
            for k, v in element.items():
                if k not in element.posArgs:
                    args.append("%s=%s" % (str(k), repr(v)))
            if not element.subElements:
                output.write('%s%s(%s)'
                    % (level*'    ', element.elementType, ', '.join(args)))
            else:
                output.write('%s%s(%s)[\n'
                    % (level*'    ', element.elementType, ', '.join(args)))
                self.write(element.subElements, output, level+1)
                output.write(']')
            if level == 0:
                output.write('\n')
            elif idx < len(elements) - 1:
                output.write(',\n')


def toStr(value):
    if isinstance(value, unicode):
        return value.encode('UTF-8')
    return str(value)
