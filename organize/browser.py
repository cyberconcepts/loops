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
from zope.app.authentication.principalfolder import InternalPrincipal
from zope.app.form.browser.textwidgets import PasswordWidget as BasePasswordWidget
from zope.app.form.interfaces import WidgetInputError
from zope.app.principalannotation import annotations
from zope.cachedescriptors.property import Lazy
from zope.formlib.form import Form as FormlibForm, FormFields, action
from zope.formlib.namedtemplate import NamedTemplate
from zope.i18nmessageid import MessageFactory

from cybertools.composer.schema.browser.common import schema_macros
from cybertools.composer.schema.browser.form import Form
from cybertools.composer.schema.schema import FormState, FormError
from cybertools.typology.interfaces import IType
from loops.browser.concept import ConceptView
from loops.browser.node import NodeView
from loops.browser.concept import ConceptRelationView
from loops.organize.interfaces import ANNOTATION_KEY, IMemberRegistrationManager
from loops.organize.interfaces import IMemberRegistration, IPasswordChange
from loops.organize.party import getPersonForUser
from loops.organize.util import getInternalPrincipal
import loops.browser.util
from loops.util import _


class MyStuff(ConceptView):

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.person = getPersonForUser(context, request)
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


class MemberRegistration(NodeView, FormlibForm):

    form_fields = FormFields(IMemberRegistration).omit('age')
    form_fields['password'].custom_widget = PasswordWidget
    template = loops.browser.util.dataform
    label = _(u'Member Registration')

    def __init__(self, context, request, testing=False):
        super(MemberRegistration, self).__init__(context, request)
        if not testing:
            self.setUpWidgets()

    @Lazy
    def macro(self):
        return self.template.macros['content']

    @Lazy
    def item(self):
        return self

    def update(self):
        # see cybertools.browser.view.GenericView.update()
        NodeView.update(self)
        Form.update(self)
        return True

    @action(_(u'Register'))
    def handle_register_action(self, action, data):
        print 'register'
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


class PasswordChange(NodeView, Form):

    interface = IPasswordChange
    message = u'Your password has been changed.'

    formErrors = dict(
        confirm_nomatch=FormError(u'Password and password confirmation do not match.'),
        wrong_oldpw=FormError(u'Your old password was not entered correctly.'),
    )

    label = label_submit = u'Change Password'

    @Lazy
    def macro(self):
        return schema_macros.macros['form']

    @Lazy
    def item(self):
        return self

    @Lazy
    def data(self):
        data = dict(oldPassword=u'', password=u'', passwordConfirm=u'')
        return data

    def update(self):
        form = self.request.form
        if not form.get('action'):
            return True
        formState = self.formState = self.validate(form)
        if formState.severity > 0:
            return True
        pw = form.get('password')
        pwConfirm = form.get('passwordConfirm')
        if pw != pwConfirm:
            fi = formState.fieldInstances['password']
            fi.setError('confirm_nomatch', self.formErrors)
            formState.severity = max(formState.severity, fi.severity)
            return True
        oldPw = form.get('oldPassword')
        regMan = IMemberRegistrationManager(self.context.getLoopsRoot())
        principal = self.request.principal
        result = regMan.changePassword(principal, oldPw, pw)
        if not result:
            fi = formState.fieldInstances['oldPassword']
            fi.setError('wrong_oldpw', self.formErrors)
            formState.severity = max(formState.severity, fi.severity)
            return True
        url = '%s?messsage=%s' % (self.url, self.message)
        self.request.response.redirect(url)
        return False

    def validate(self, data):
        formState = FormState()
        for f in self.schema.fields:
            fi = f.getFieldInstance()
            value = data.get(f.name)
            fi.validate(value, data)
            formState.fieldInstances.append(fi)
            formState.severity = max(formState.severity, fi.severity)
        return formState

