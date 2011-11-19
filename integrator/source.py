#
#  Copyright (c) 2011 Helmut Merz helmutm@cy55.de
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
Managing information form objects provided by external sources, e.g. loops.agent.
"""

from persistent.mapping import PersistentMapping
from zope import interface, component
from zope.interface import implements
from zope.component import adapts

from loops.common import adapted
from loops.interfaces import ILoopsObject
from loops.integrator.interfaces import IExternalSourceInfo


sourceInfoAttrName = '__loops_integrator_sourceinfo__'


class ExternalSourceInfo(object):

    implements(IExternalSourceInfo)
    adapts(ILoopsObject)

    def __init__(self, context):
        self.context = self.__parent__ = context

    def getSourceInfo(self):
        return getattr(self.context, sourceInfoAttrName, PersistentMapping())

    def getExternalIdentifier(self):
        # first try to find adapter on adapted concept or resource
        adobj = adapted(self.context)
        if adobj != self.context:
            adaptedSourceInfo = IExternalSourceInfo(adobj, None)
            if adaptedSourceInfo is not None:
                return adaptedSourceInfo.externalIdentifier
        # otherweise use stored external identifier
        return self.getSourceInfo().get('externalIdentifier')
    def setExternalIdentifier(self, value):
        info = self.getSourceInfo()
        if not info:
            setattr(self.context, sourceInfoAttrName, info)
        info['externalIdentifier'] = value
    externalIdentifier = property(getExternalIdentifier, setExternalIdentifier)

