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
Basic implementation of the elements used for the intermediate format for export
and import of loops objects.

$Id$
"""

from zope.cachedescriptors.property import Lazy
from zope.dottedname.resolve import resolve
from zope.interface import implements
from zope.traversing.api import getName

from loops.external.interfaces import IElement


class Element(dict):

    implements(IElement)

    elementType = ''

    def __init__(self, name, title, type=None, *args, **kw):
        self['name'] = name
        self['title'] = title
        if type:
            self['type'] = type
        for k, v in kw.items():
            self[k] = v

    def __call__(self, loader):
        pass


class ConceptElement(Element):

    elementType = 'concept'
    posArgs = ('name', 'title', 'type')

    def __call__(self, loader):
        type = loader.concepts[self['type']]
        kw = dict((k, v) for k, v in self.items()
                         if k not in ('name', 'title', 'type'))
        loader.addConcept(self['name'], self['title'], type, **kw)


class TypeElement(ConceptElement):

    elementType = 'type'
    posArgs = ('name', 'title')

    def __init__(self, name, title, *args, **kw):
        super(TypeElement, self).__init__(name, title, *args, **kw)
        ti = self['typeInterface']
        if ti:
            self['typeInterface'] = '.'.join((ti.__module__, ti.__name__))
        else:
            del self['typeInterface']

    def __call__(self, loader):
        kw = dict((k, v) for k, v in self.items()
                if k not in ('name', 'title', 'type', 'typeInterface'))
        kw['typeInterface'] = resolve(self['typeInterface'])
        loader.addConcept(self['name'], self['title'], 'type', **kw)


class ResourceElement(ConceptElement):

    elementType = 'resource'


class ChildElement(Element):

    elementType = 'child'
    posArgs = ('first', 'second', 'predicate', 'order', 'relevance')

    def __init__(self, *args):
        for idx, arg in enumerate(args):
            self[self.posArgs[idx]] = arg

    def __call__(self, loader):
        loader.assignChild(self['first'], self['second'], self['predicate'])


elementTypes = dict(
    type=TypeElement,
    concept=ConceptElement,
    resource=ResourceElement,
    child=ChildElement,
)
