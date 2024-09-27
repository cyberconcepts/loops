# loops.compound.microart.base

""" Micro articles (MicroArt).
"""

from zope.cachedescriptors.property import Lazy
from zope.dublincore.interfaces import IZopeDublinCore
from zope.interface import implementer
from zope.event import notify
from zope.lifecycleevent import ObjectCreatedEvent, ObjectModifiedEvent
from zope import schema
from zope.traversing.api import getName

from loops.common import adapted
from loops.compound.base import Compound
from loops.compound.microart.interfaces import IMicroArt
from loops.resource import Resource
from loops.setup import addAndConfigureObject
from loops.type import TypeInterfaceSourceList


TypeInterfaceSourceList.typeInterfaces += (IMicroArt,)


@implementer(IMicroArt)
class MicroArt(Compound):

    _contextAttributes = list(IMicroArt)
    _adapterAttributes = Compound._adapterAttributes + ('story',)
    _noexportAttributes = ('story',)
    _textIndexAttributes = ('story', 'insight', 'consequences', 'folloUps')

    defaultTextContentType = 'text/html'
    textContentType = defaultTextContentType

    def getStory(self):
        res = self.getParts()
        if len(res) > 0:
            return adapted(res[0]).data
        return u''
    def setStory(self, value):
        res = self.getParts()
        if len(res) > 0:
            res = adapted(res[0])
        else:
            tTextDocument = self.conceptManager['textdocument']
            name = getName(self.context) + '_story'
            res = addAndConfigureObject(self.resourceManager, Resource, name,
                    title=self.title, contentType=self.defaultTextContentType,
                    resourceType=tTextDocument)
            #notify(ObjectCreatedEvent(res))
            self.add(res, position=0)
            res = adapted(res)
        res.data = value
        notify(ObjectModifiedEvent(res.context))
    story = property(getStory, setStory)
