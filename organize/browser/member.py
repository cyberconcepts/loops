#
#  Copyright (c) 2008 Helmut Merz helmutm@cy55.de
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
Definition of view classes and other browser related stuff for
members (persons).

$Id$
"""

from zope import interface, component
from zope.app.authentication.principalfolder import InternalPrincipal
from zope.app.form.browser.textwidgets import PasswordWidget as BasePasswordWidget
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.app.principalannotation import annotations
from zope.cachedescriptors.property import Lazy
from zope.i18nmessageid import MessageFactory

from cybertools.composer.interfaces import IInstance
from cybertools.composer.schema.browser.common import schema_macros
from cybertools.composer.schema.browser.form import Form, CreateForm
from cybertools.composer.schema.schema import FormState, FormError
from cybertools.typology.interfaces import IType
from loops.browser.common import concept_macros
from loops.browser.concept import ConceptView, ConceptRelationView
from loops.browser.node import NodeView
from loops.concept import Concept
from loops.organize.interfaces import ANNOTATION_KEY, IMemberRegistrationManager
from loops.organize.interfaces import IMemberRegistration, IPasswordChange
from loops.organize.party import getPersonForUser, Person
from loops.organize.util import getInternalPrincipal
import loops.browser.util
from loops.util import _


organize_macros = ViewPageTemplateFile('view_macros.pt')


class PersonalInfo(ConceptView):

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.person = getPersonForUser(context, request)
        if self.person is not None:
            self.context = self.person

    @Lazy
    def macro(self):
        return organize_macros.macros['conceptdata']

    @Lazy
    def concept_macros(self):
        return concept_macros

    @Lazy
    def view(self):
        return self


class MemberRegistration(NodeView, CreateForm):

    interface = IMemberRegistration
    message = _(u'The user account has been created.')

    formErrors = dict(
        confirm_nomatch=FormError(_(u'Password and password confirmation do not match.')),
        duplicate_loginname=FormError(_('Login name already taken.')),
    )

    label = _(u'Member Registration')
    label_submit = _(u'Register')

    permissions_key = u'registration.permissions'
    roles_key = u'registration.roles'
    registration_adapter_key = u'registration.adapter'

    @Lazy
    def macro(self):
        return schema_macros.macros['form']

    @Lazy
    def item(self):
        return self

    @Lazy
    def schema(self):
        schema = super(MemberRegistration, self).schema
        schema.fields.remove('birthDate')
        schema.fields.reorder(-2, 'loginName')
        return schema

    @Lazy
    def object(self):
        return Person(Concept())

    def update(self):
        form = self.request.form
        if not form.get('action'):
            return True
        instance = component.getAdapter(self.object, IInstance, name='editor')
        instance.template = self.schema
        self.formState = formState = instance.applyTemplate(data=form,
                                            fieldHandlers=self.fieldHandlers)
        if formState.severity > 0:
            # show form again
            return True
        pw = form.get('password')
        if form.get('passwordConfirm') != pw:
            fi = formState.fieldInstances['password']
            fi.setError('confirm_nomatch', self.formErrors)
            formState.severity = max(formState.severity, fi.severity)
            return True
        login = form.get('loginName')
        regMan = IMemberRegistrationManager(self.context.getLoopsRoot())
        result = regMan.register(login, pw,
                                 form.get('lastName'), form.get('firstName'),
                                 email=form.get('email'),
                                 phoneNumbers=form.get('phoneNumbers'))
        if isinstance(result, dict):
            fi = formState.fieldInstances[result['fieldName']]
            fi.setError(result['error'], self.formErrors)
            formState.severity = max(formState.severity, fi.severity)
            return True
        self.object = result
        msg = self.message
        #self.request.response.redirect('%s/login.html?login=%s&message=%s'
        #                    % (self.url, login, msg))
        self.request.response.redirect('%s?message=%s' % (self.url, msg))
        return False


class PasswordChange(NodeView, Form):

    interface = IPasswordChange
    message = _(u'Your password has been changed.')

    formErrors = dict(
        confirm_nomatch=FormError(_(u'Password and password confirmation do not match.')),
        wrong_oldpw=FormError(_(u'Your old password was not entered correctly.')),
    )

    label = label_submit = _(u'Change Password')

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

