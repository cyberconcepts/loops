# loops.external.pyfunc

""" Reading and writing loops objects (represented by IElement objects)
in Python function notation.
"""

from zope.cachedescriptors.property import Lazy
from zope.interface import implementer

from loops.external.interfaces import IReader, IWriter
from loops.external.element import elementTypes, toplevelElements


@implementer(IReader)
class PyReader(object):

    def read(self, input):
        if not isinstance(input, str):
            input = input.read()
        proc = InputProcessor()
        exec(input, proc)
        return proc.elements


class InputProcessor(dict):

    _constants = {'True': True, 'False': False}

    def __init__(self):
        self.elements = []
        self['__builtins__'] = dict()   # security!

    def __getitem__(self, key):
        if key in self._constants:
            return self._constants[key]
        def factory(*args, **kw):
            element = elementTypes[key](*args, **kw)
            if key in toplevelElements:
                self.elements.append(element)
            return element
        return factory


@implementer(IWriter)
class PyWriter(object):

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
