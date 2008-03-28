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
Export/import of annotations.

$Id$
"""

from zope.component import adapts
from zope.interface import implements

from loops.external.element import Element, elementTypes
from loops.external.interfaces import ISubExtractor
from loops.interfaces import ILoopsObject


class AnnotationsElement(Element):

    elementType = 'annotations'

    def __init__(self, **kw):
        for k, v in kw.items():
            self[k] = v

    def __call__(self, loader):
        print self.items()


class AnnotationsExtractor(object):

    implements(ISubExtractor)
    adapts(ILoopsObject)

    def extract(self):
        return []


elementTypes.update(dict(
    annotations=AnnotationsElement,
))

