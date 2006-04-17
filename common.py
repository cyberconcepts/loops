#
#  Copyright (c) 2006 Helmut Merz helmutm@cy55.de
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
Common stuff.

$Id$
"""

from zope.app import zapi
from zope.app.dublincore.interfaces import IZopeDublinCore
from zope.app.dublincore.annotatableadapter import ZDCAnnotatableAdapter
from zope.app.dublincore.zopedublincore import ScalarProperty
from zope.component import adapts
from zope.interface import implements
from zope.cachedescriptors.property import Lazy
from loops.interfaces import ILoopsObject


class LoopsDCAdapter(ZDCAnnotatableAdapter):

    implements(IZopeDublinCore)
    adapts(ILoopsObject)

    def __init__(self, context):
        self.context = context
        super(LoopsDCAdapter, self).__init__(context)

    def Title(self):
        return super(LoopsDCAdapter, self).title or self.context.title
    def setTitle(self, value):
        ScalarProperty(u'Title').__set__(self, value)
    title = property(Title, setTitle)


