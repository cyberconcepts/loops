# loops.integrator.source

""" Managing information form objects provided by external sources, e.g. loops.agent.
"""

from persistent.mapping import PersistentMapping
from zope import interface, component
from zope.interface import implementer
from zope.component import adapts

from loops.common import adapted, AdapterBase
from loops.interfaces import ILoopsObject
from loops.integrator.interfaces import IExternalSourceInfo


sourceInfoAttrName = '__loops_integrator_sourceinfo__'


@implementer(IExternalSourceInfo)
class ExternalSourceInfo(object):

    adapts(ILoopsObject)

    def __init__(self, context):
        #import pdb; pdb.set_trace()
        self.context = self.__parent__ = context

    def getSourceInfo(self):
        return getattr(self.context, sourceInfoAttrName, PersistentMapping())

    def getExternalIdentifier(self):
        # first try to find adapter on adapted concept or resource
        adobj = adapted(self.context)
        #if adobj != self.context:
        #if not adobj is self.context:
        if isinstance(adobj, AdapterBase):
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

