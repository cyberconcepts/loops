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
Common base class for loops browser view classes.

$Id$
"""

from zope.app import zapi
from zope import component
from zope.app.form.browser.interfaces import ITerms
from zope.cachedescriptors.property import Lazy
from zope.dottedname.resolve import resolve
from zope.dublincore.interfaces import IZopeDublinCore
from zope.formlib import form
from zope.formlib.form import FormFields
from zope.formlib.namedtemplate import NamedTemplate
from zope.interface import Interface, implements
from zope.publisher.browser import applySkin
#from zope.publisher.interfaces.browser import ISkin
from zope.publisher.interfaces.browser import IBrowserSkinType
from zope import schema
from zope.schema.vocabulary import SimpleTerm
from zope.security import canAccess, canWrite
from zope.security.proxy import removeSecurityProxy
from zope.traversing.browser import absoluteURL
from zope.traversing.api import getName

from cybertools.browser.view import GenericView
from cybertools.relation.interfaces import IRelationRegistry
from cybertools.typology.interfaces import IType, ITypeManager
from loops.interfaces import IView
from loops.resource import Resource
from loops.type import ITypeConcept
from loops import util
from loops.util import _


class NameField(schema.ASCIILine):

    def _validate(self, value):
        super(NameField, self)._validate(value)


class IAddForm(Interface):

    name = NameField(
            title=_(u'Object name'),
            description=_(u'Name of the object - will be used for addressing the '
                        'object via a URL; should therefore be unique within '
                        'the container and not contain special characters')
        )


class AddForm(form.AddForm):

    form_fields = FormFields(IAddForm)
    template = NamedTemplate('loops.pageform')


class EditForm(form.EditForm):

    template = NamedTemplate('loops.pageform')

    def deleteObjectAction(self):
        return None  # better not to show the edit button at the moment
        parent = zapi.getParent(self.context)
        parentUrl = absoluteURL(parent, self.request)
        return parentUrl + '/contents.html'


class BaseView(GenericView):

    def __init__(self, context, request):
        # TODO: get rid of removeSecurityProxy() call
        super(BaseView, self).__init__(context, request)
        self.context = removeSecurityProxy(context)
        self.setSkin(self.loopsRoot.skinName)

    def setSkin(self, skinName):
        skin = None
        if skinName and IView.providedBy(self.context):
            skin = component.queryUtility(IBrowserSkinType, skinName)
            if skin:
                applySkin(self.request, skin)
        self.skin = skin

    @Lazy
    def modified(self):
        """ get date/time of last modification
        """
        dc = IZopeDublinCore(self.context)
        d = dc.modified or dc.created
        return d and d.strftime('%Y-%m-%d %H:%M') or ''

    @Lazy
    def loopsRoot(self):
        return self.context.getLoopsRoot()

    @Lazy
    def url(self):
        return absoluteURL(self.context, self.request)

    @Lazy
    def view(self):
        return self

    @Lazy
    def token(self):
        return self.loopsRoot.getLoopsUri(self.context)

    @Lazy
    def title(self):
        return self.context.title or getName(self.context)

    @Lazy
    def description(self):
        return self.context.description

    @Lazy
    def dcTitle(self):
        return IZopeDublinCore(self.context).title or self.title

    @Lazy
    def headTitle(self):
        return self.dcTitle

    @Lazy
    def value(self):
        return self.context

    @Lazy
    def uniqueId(self):
        return util.getUidForObject(self.context)

    # type stuff

    @Lazy
    def type(self):
        return IType(self.context)

    @Lazy
    def typeProvider(self):
        return self.type.typeProvider

    @Lazy
    def typeInterface(self):
        return self.type.typeInterface

    @Lazy
    def typeAdapter(self):
        ifc = self.typeInterface
        if ifc is not None:
            return ifc(self.context)

    @Lazy
    def typeTitle(self):
        return self.type.title

    @Lazy
    def typeUrl(self):
        provider = self.typeProvider
        if provider is not None:
            return absoluteURL(provider, self.request)
        return None

    def viewIterator(self, objs):
        request = self.request
        for o in objs:
            yield BaseView(o, request)

    # type listings

    def listTypes(self, include=None, exclude=None, sortOn='title'):
        types = [dict(token=t.token, title=t.title)
                    for t in ITypeManager(self.context).listTypes(include, exclude)]
        if sortOn:
            types.sort(key=lambda x: x[sortOn])
        return types

    def resourceTypes(self):
        return util.KeywordVocabulary(self.listTypes(('resource',), ('hidden',)))
            #if t.factory == Resource]) # ? if necessary -> type.qualifiers

    def conceptTypes(self):
        return util.KeywordVocabulary(self.listTypes(('concept',), ('hidden',)))

    def listTypesForSearch(self, include=None, exclude=None, sortOn='title'):
        types = [dict(token=t.tokenForSearch, title=t.title)
                    for t in ITypeManager(self.context).listTypes(include, exclude)]
        if sortOn:
            types.sort(key=lambda x: x[sortOn])
        return types

    def typesForSearch(self):
        general = [('loops:resource:*', 'Any Resource'),
                   ('loops:concept:*', 'Any Concept'),]
        return util.KeywordVocabulary(general
                            + self.listTypesForSearch(exclude=('system', 'hidden',))
                            + [('loops:*', 'Any')])

    def conceptTypesForSearch(self):
        general = [('loops:concept:*', 'Any Concept'),]
        return util.KeywordVocabulary(general
                            + self.listTypesForSearch(('concept',), ('system', 'hidden',),))

    def resourceTypesForSearch(self):
        general = [('loops:resource:*', 'Any Resource'),]
        return util.KeywordVocabulary(general
                            + self.listTypesForSearch(('resource',), ('system', 'hidden'),))

    # controllling editing

    @Lazy
    def editable(self):
        return canWrite(self.context, 'title')

    def getActions(self, category):
        """ Return a list of actions that provide the view and edit actions
            available for the context object.
        """
        return []

    def openEditWindow(self, viewName='edit.html'):
        if self.editable:
            return "openEditWindow('%s/@@%s')" % (self.url, viewName)
        return ''

    @Lazy
    def xeditable(self):
        return self.request.principal.id == 'rootadmin'
        #return getattr(self.context, 'contentType', '').startswith('text/')

    @Lazy
    def inlineEditingActive(self):
        #return False
        #return self.request.principal.id == 'rootadmin'
        # this may depend on system and user settings...
        return True

    inlineEditable = False

    def inlineEdit(self, id):
        self.registerDojo()
        return 'return inlineEdit("%s", "")' % id

    def registerDojo(self):
        cm = self.controller.macros
        cm.register('js', 'dojo.js', resourceName='ajax.dojo/dojo.js')


# actions

class Action(object):

    def __init__(self, renderer, url, **kw):
        self.renderer = renderer
        self.url = url
        self.__dict__.update(kw)
        #for k in kw:
        #    setattr(self, k, kw[k])


# vocabulary stuff

class LoopsTerms(object):
    """ Provide the ITerms interface, e.g. for usage in selection
        lists.
    """

    implements(ITerms)

    def __init__(self, source, request):
        # the source parameter is a view or adapter of a real context object:
        self.source = source
        self.context = source.context
        self.request = request

    @Lazy
    def loopsRoot(self):
        return self.context.getLoopsRoot()

    def getTerm(self, value):
        #if value is None:
        #    return SimpleTerm(None, '', u'not assigned')
        title = value.title or zapi.getName(value)
        token = self.loopsRoot.getLoopsUri(value)
        return SimpleTerm(value, token, title)

    def getValue(self, token):
        return self.loopsRoot.loopsTraverse(token)


class InterfaceTerms(object):
    """ Provide the ITerms interface for source list of interfaces.
    """

    implements(ITerms)

    def __init__(self, source, request):
        self.source = source
        self.request = request

    def getTerm(self, value):
        token = '.'.join((value.__module__, value.__name__))
        return SimpleTerm(value, token, token)

    def getValue(self, token):
        return resolve(token)


