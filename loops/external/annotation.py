# loops.external.annotation

""" Export/import of annotations.
"""

from datetime import datetime
import time
from zope.component import adapts
from zope.dublincore.interfaces import IZopeDublinCore
from zope.interface import implementer

from loops.external.element import Element, elementTypes
from loops.external.interfaces import ISubExtractor
from loops.interfaces import ILoopsObject


class AnnotationsElement(Element):

    elementType = 'annotations'

    def __init__(self, **kw):
        for k, v in kw.items():
            self[k] = v

    def execute(self, loader):
        obj = self.parent.object
        dc = IZopeDublinCore(obj, None)
        if dc is not None:
            for k, v in self.items():
                if k in ('created', 'modified'):
                    v = datetime(*time.strptime(v, u'%Y-%m-%dT%H:%M')[0:6])
                setattr(dc, k, v)


@implementer(ISubExtractor)
class AnnotationsExtractor(object):

    adapts(ILoopsObject)

    dcAttributes = ('title', 'description', 'creators', 'created', 'modified')

    def __init__(self, context):
        self.context = context

    def extract(self):
        dc = IZopeDublinCore(self.context, None)
        if dc is not None:
            result = {}
            for attr in self.dcAttributes:
                value = getattr(dc, attr, None)
                if attr in ('title',):
                    if value == getattr(self.context, attr):
                        value = None
                if value:
                    if attr in ('created', 'modified'):
                        value = value.strftime('%Y-%m-%dT%H:%M')
                    result[attr] = value
            if result:
                yield AnnotationsElement(**result)


elementTypes.update(dict(
    annotations=AnnotationsElement,
))

