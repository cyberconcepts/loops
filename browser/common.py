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
from zope.app.dublincore.interfaces import IZopeDublinCore
from zope.app.form.browser.interfaces import ITerms
from zope.app.intid.interfaces import IIntIds
from zope.cachedescriptors.property import Lazy
from zope.dottedname.resolve import resolve
from zope.formlib.form import FormFields
from zope.formlib.form import EditForm as BaseEditForm
from zope.formlib.form import AddForm as BaseAddForm
from zope.formlib.namedtemplate import NamedTemplate
from zope.interface import Interface, implements
from zope.app.publisher.browser import applySkin
from zope.publisher.interfaces.browser import ISkin
from zope import schema
from zope.schema.vocabulary import SimpleTerm
from zope.security import canAccess, canWrite
from zope.security.proxy import removeSecurityProxy

from cybertools.typology.interfaces import IType
from loops.interfaces import IView
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


class AddForm(BaseAddForm):

    form_fields = FormFields(IAddForm)
    template = NamedTemplate('loops.pageform')


class EditForm(BaseEditForm):

    template = NamedTemplate('loops.pageform')

    def deleteObjectAction(self):
        return None  # better not to show the edit button at the moment
        parent = zapi.getParent(self.context)
        parentUrl = zapi.absoluteURL(parent, self.request)
        return parentUrl + '/contents.html'


class BaseView(object):

    def __init__(self, context, request):
        #self.context = context
        # TODO: get rid of removeSecurityProxy() call
        self.context = removeSecurityProxy(context)
        self.request = request
        self.setSkin(self.loopsRoot.skinName)

    def setSkin(self, skinName):
        skin = None
        if skinName and IView.providedBy(self.context):
            skin = zapi.queryUtility(ISkin, skinName)
            if skin:
                applySkin(self.request, skin)
        self.skin = skin

    _controller = None
    def setController(self, controller):
        self._controller = controller
        # this is also the place to register special macros with the controller
        if getattr(controller, 'skinName', None):
            self.setSkin(controller.skinName.value)
        controller.skin = self.skin
    def getController(self): return self._controller
    controller = property(getController, setController)

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
        return zapi.absoluteURL(self.context, self.request)

    @Lazy
    def view(self):
        return self

    @Lazy
    def token(self):
        return self.loopsRoot.getLoopsUri(self.context)

    @Lazy
    def title(self):
        return self.context.title or zapi.getName(self.context)

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
    def typeTitle(self):
        type = IType(self.context)
        return type is not None and type.title or None

    @Lazy
    def typeUrl(self):
        type = IType(self.context)
        if type is not None:
            provider = type.typeProvider
            if provider is not None:
                return zapi.absoluteURL(provider, self.request)
        return None

    def viewIterator(self, objs):
        request = self.request
        for o in objs:
            yield BaseView(o, request)

    @Lazy
    def uniqueId(self):
        return zapi.getUtility(IIntIds).getId(self.context)

    @Lazy
    def editable(self):
        return canWrite(self.context, 'title')

    def openEditWindow(self, viewName='edit.html'):
        if self.editable:
            return "openEditWindow('%s/@@%s')" % (self.url, viewName)
        return ''

    @Lazy
    def xeditable(self):
        return getattr(self.context, 'contentType', '').startswith('text/')


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


