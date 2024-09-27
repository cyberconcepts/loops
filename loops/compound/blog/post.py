# loops.compound.blog.post

""" Blogs and blog posts.
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
from loops.compound.blog.interfaces import ISimpleBlogPost, IBlogPost
from loops.resource import Resource
from loops.security.common import restrictView
from loops.setup import addAndConfigureObject
from loops.type import TypeInterfaceSourceList


TypeInterfaceSourceList.typeInterfaces += (ISimpleBlogPost, IBlogPost,)


@implementer(ISimpleBlogPost)
class SimpleBlogPost(Compound):

    textContentType = 'text/html'

    _adapterAttributes = Compound._adapterAttributes + ('creator',)
    _contextAttributes = list(ISimpleBlogPost)
    _noexportAttributes = _adapterAttributes
    _textIndexAttributes = ('text',)

    @property
    def creator(self):
        cr = IZopeDublinCore(self.context).creators
        return cr and cr[0] or None


@implementer(IBlogPost)
class BlogPost(Compound):

    _adapterAttributes = Compound._adapterAttributes + ('text', 'private', 'creator',)
    _contextAttributes = Compound._contextAttributes + ['date', 'privateComment']
    _noexportAttributes = ('creator', 'text', 'private')
    _textIndexAttributes = ('text',)

    defaultTextContentType = 'text/restructured'
    textContentType = defaultTextContentType

    @Lazy
    def isPartOf(self):
        return self.context.getLoopsRoot().getConceptManager()['ispartof']

    def getPrivate(self):
        return getattr(self.context, '_private', False)
    def setPrivate(self, value):
        self.context._private = value
        restrictView(self.context, revert=not value)
        for r in self.context.getResources([self.isPartOf], noSecurityCheck=True):
            restrictView(r, revert=not value)
    private = property(getPrivate, setPrivate)

    def getText(self):
        res = self.getParts()
        if len(res) > 0:
            return adapted(res[0]).data
        return u''
    def setText(self, value):
        res = self.getParts()
        if len(res) > 0:
            res = adapted(res[0])
        else:
            tTextDocument = self.conceptManager['textdocument']
            name = getName(self.context) + '_text'
            res = addAndConfigureObject(self.resourceManager, Resource, name,
                    title=self.title, contentType=self.defaultTextContentType,
                    resourceType=tTextDocument)
            #notify(ObjectCreatedEvent(res))
            self.add(res, position=0)
            res = adapted(res)
        res.data = value
        notify(ObjectModifiedEvent(res.context))
    text = property(getText, setText)

    @property
    def creator(self):
        cr = IZopeDublinCore(self.context).creators
        return cr and cr[0] or None

