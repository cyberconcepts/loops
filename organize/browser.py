#
#  Copyright (c) 2004 Helmut Merz helmutm@cy55.de
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
Definition of view classes and other browser related stuff for the
loops.organize package.

$Id$
"""

from zope import interface, component
from zope.app import zapi
from zope.app.form.browser.textwidgets import PasswordWidget as BasePasswordWidget
from zope.app.form.interfaces import WidgetInputError
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.app.principalannotation import annotations
from zope.cachedescriptors.property import Lazy
from zope.formlib.form import Form, FormFields, action
from zope.formlib.namedtemplate import NamedTemplate
from zope.i18nmessageid import MessageFactory

from cybertools.typology.interfaces import IType
from loops.browser.concept import ConceptView
from loops.browser.node import NodeView
from loops.browser.concept import ConceptRelationView
from loops.organize.interfaces import ANNOTATION_KEY, IMemberRegistrationManager
from loops.organize.interfaces import IMemberRegistration

_ = MessageFactory('zope')


def getPersonForLoggedInUser(request):
        pa = annotations(request.principal)
        return  pa.get(ANNOTATION_KEY, None)


class MyStuff(ConceptView):

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.person = getPersonForLoggedInUser(request)
        if self.person is not None:
            self.context = self.person

    @Lazy
    def view(self):
        return self


class PasswordWidget(BasePasswordWidget):

    def getInputValue(self):
        value = super(PasswordWidget, self).getInputValue()
        confirm = self.request.get('form.passwordConfirm')
        if confirm != value:
            v = _(u'Password and password confirmation do not match.')
            self._error = WidgetInputError(
                self.context.__name__, self.label, v)
            raise self._error
        return value


class MemberRegistration(Form, NodeView):

    form_fields = FormFields(IMemberRegistration)
    template = NamedTemplate('loops.dataform')
    label = _(u'Member Registration')

    def __init__(self, context, request):
        NodeView.__init__(self, context, request)

    @action(_(u'Register'))
    def handle_register_action(self, action, data):
        self.register(data)

    def register(self, data=None):
        form = data or self.request.form
        pw = form.get('password')
        if form.get('passwordConfirm') != pw:
            raise ValueError(u'Password and password confirmation do not match.')
        login = form.get('loginName')
        regMan = IMemberRegistrationManager(self.context.getLoopsRoot())
        person = regMan.register(login, pw,
                                 form.get('lastName'),
                                 form.get('firstName'))
        message = _(u'You have been registered and can now login.')
        self.request.response.redirect('%s/login.html?login=%s&message=%s'
                            % (self.url, login, message))
        return person

