#
#  Copyright (c) 2013 Helmut Merz helmutm@cy55.de
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
"""

from datetime import datetime
from email.MIMEText import MIMEText
from zope import interface, component
from zope.app.authentication.principalfolder import InternalPrincipal
from zope.app.form.browser.textwidgets import PasswordWidget as BasePasswordWidget
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.app.principalannotation import annotations
from zope.cachedescriptors.property import Lazy
from zope.i18nmessageid import MessageFactory
from zope.security import checkPermission
from zope.sendmail.interfaces import IMailDelivery
from zope.traversing.browser import absoluteURL

from cybertools.composer.interfaces import IInstance
from cybertools.composer.schema.browser.common import schema_macros
from cybertools.composer.schema.browser.form import Form, CreateForm
from cybertools.composer.schema.schema import FormState, FormError
from cybertools.meta.interfaces import IOptions
from cybertools.typology.interfaces import IType
from cybertools.util.randomname import generateName
from loops.browser.common import concept_macros, form_macros
from loops.browser.concept import ConceptView, ConceptRelationView
from loops.browser.node import NodeView
from loops.common import adapted
from loops.concept import Concept
from loops.organize.interfaces import ANNOTATION_KEY, IMemberRegistrationManager
from loops.organize.interfaces import IMemberRegistration, IPasswordChange
from loops.organize.party import getPersonForUser, Person
from loops.organize.util import getInternalPrincipal, getPrincipalForUserId
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


class BaseMemberRegistration(NodeView):

    interface = IMemberRegistration     # TODO: add company, create institution
    message = _(u'The user account has been created.')
    template = form_macros

    formErrors = dict(
        confirm_nomatch=FormError(_(u'Password and password confirmation do not match.')),
        duplicate_loginname=FormError(_('Login name already taken.')),
    )

    label = _(u'Member Registration')
    label_submit = _(u'Register')
    title = _('Member Registration')

    permissions_key = u'registration.permissions'
    roles_key = u'registration.roles'
    registration_adapter_key = u'registration.adapter'
    text_names_prefix = 'organize.member.registration'
    # texts: reg_info, reg_feedback, conf_mail, conf_info, conf_feedback
    info_key = 'reg_info'
    feedback_key = 'reg_feedback'

    isInnerHtml = False
    showAssignments = False
    form_action = 'register'
    versionInfo = None

    def closeAction(self, submit=True):
        return u''

    @Lazy
    def macro(self):
        #return schema_macros.macros['form']
        return organize_macros.macros['register']

    def checkPermissions(self):
        personType = adapted(self.conceptManager['person'])
        perms = IOptions(personType)(self.permissions_key)
        if perms:
            return checkPermission(perms[0], self.context)
        return checkPermission('loops.ManageSite', self.context)

    @Lazy
    def item(self):
        return self

    @Lazy
    def data(self):
        return self.request.form

    def getPrincipalAnnotation(self, principal):
        return annotations(principal).get(ANNOTATION_KEY, None)

    @Lazy
    def infoText(self):
        name = '.'.join((self.text_names_prefix, self.info_key))
        text = self.resourceManager.get(name)
        if text:
            return self.renderText(text.data, text.contentType)
        return u''

    @Lazy
    def feedbackUrl(self):
        name = '.'.join((self.text_names_prefix, self.feedback_key))
        text = self.resourceManager.get(name)
        if text:
            return self.getUrlForTarget(text)


class MemberRegistration(BaseMemberRegistration, CreateForm):

    @Lazy
    def schema(self):
        schema = super(MemberRegistration, self).schema
        schema.fields.remove('birthDate')
        schema.fields.reorder(-2, 'loginName')
        return schema
    # TODO: add company, create institution

    @Lazy
    def object(self):
        return Person(Concept())

    def update(self):
        form = self.request.form
        if not form.get('form.action'):
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
        phoneNumbers = [x.strip()
                            for x in (form.get('phoneNumbers') or u'').split('\n')]
        result = regMan.register(login, pw,
                                 form.get('lastName'), form.get('firstName'),
                                 email=form.get('email'),
                                 phoneNumbers=[x for x in phoneNumbers if x])
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


class SecureMemberRegistration(BaseMemberRegistration, CreateForm):

    permissions_key = u'secure_registration.permissions'
    roles_key = u'secure_registration.roles'
    email_key = 'reg_email'

    @Lazy
    def schema(self):
        schema = super(SecureMemberRegistration, self).schema
        schema.fields.remove('birthDate')
        schema.fields.remove('password')
        schema.fields.remove('passwordConfirm')
        schema.fields.remove('phoneNumbers')
        #schema.fields.reorder(-2, 'loginName')
        return schema

    @Lazy
    def macro(self):
        return organize_macros.macros['register']

    @Lazy
    def object(self):
        return Person(Concept())

    def update(self):
        form = self.request.form
        if not form.get('form.action'):
            return True
        instance = component.getAdapter(self.object, IInstance, name='editor')
        instance.template = self.schema
        self.formState = formState = instance.applyTemplate(data=form,
                                            fieldHandlers=self.fieldHandlers)
        if formState.severity > 0:
            # show form again
            return True
        login = form.get('loginName')
        regMan = IMemberRegistrationManager(self.context.getLoopsRoot())
        pw = generateName()
        email = form.get('email')
        try:    
            result = regMan.register(login, pw,
                                     form.get('lastName'), form.get('firstName'),
                                     email=email,)
        except ValueError, e:
            fi = formState.fieldInstances['loginName']
            fi.setError('duplicate_loginname', self.formErrors)
            formState.severity = max(formState.severity, fi.severity)
            return True
        self.object = result
        person = result.context
        pa = self.getPrincipalAnnotation(
                    getPrincipalForUserId(adapted(person).getUserId()))
        pa['id'] = generateName()
        pa['timestamp'] = datetime.utcnow()
        self.notifyEmail(login, email, pa['id'])
        if self.feedbackUrl:
            self.request.response.redirect(self.feedbackUrl)
        else:
            msg = self.message
            self.request.response.redirect('%s?loops.message=%s' % (self.url, msg))
        return False

    def notifyEmail(self, userid, recipient, id):
        baseUrl = absoluteURL(self.context.getMenu(), self.request)
        url = u'%s/selfservice_confirmation.html?login=%s&id=%s' % (
                                    baseUrl, userid, id,)
        recipients = [recipient]
        subject = _(u'confirmation_mail_subject')
        name = '.'.join((self.text_names_prefix, self.email_key))
        text = self.resourceManager.get(name)
        if text:
            message = (text.data % url).encode('UTF-8')
            subject = text.description or subject
        else:
            message = _(u'confirmation_mail_text') + u':\n\n'
            message = (message + url).encode('UTF-8')
        senderInfo = self.globalOptions('email.sender')
        sender = senderInfo and senderInfo[0] or 'info@loops.cy55.de'
        sender = sender.encode('UTF-8')
        msg = MIMEText(message, 'plain', 'utf-8')
        msg['Subject'] = subject.encode('UTF-8')
        msg['From'] = sender
        msg['To'] = ', '.join(recipients)
        mailhost = component.getUtility(IMailDelivery, 'Mail')
        mailhost.send(sender, recipients, msg.as_string())


class ConfirmMemberRegistration(BaseMemberRegistration, Form):

    permissions_key = u'secure_registration.permissions'
    roles_key = u'secure_registration.roles'
    info_key = 'confirm_info'
    feedback_key = 'confirm_feedback'
    email_key = 'confirm_email'

    form_action = 'confirm_registration'

    @Lazy
    def macro(self):
        return organize_macros.macros['confirm']

    @Lazy
    def data(self):
        form = self.request.form
        return dict(loginName=form.get('login'), id=form.get('id'))

    @Lazy
    def schema(self):
        schema = super(ConfirmMemberRegistration, self).schema
        schema.fields.remove('salutation')
        schema.fields.remove('academicTitle')
        schema.fields.remove('birthDate')
        schema.fields.remove('phoneNumbers')
        schema.fields.remove('loginName')
        schema.fields.remove('firstName')
        schema.fields.remove('lastName')
        schema.fields.remove('email')
        return schema

    def update(self):
        form = self.request.form
        if form.get('form.action') != 'confirm_registration':
            return True
        if not form.get('login'):
            return True
        regMan = IMemberRegistrationManager(self.context.getLoopsRoot())
        prefix = regMan.getPrincipalFolderFromOption().prefix
        userId = prefix + form['login']
        principal = getPrincipalForUserId(userId)
        pa = self.getPrincipalAnnotation(principal)
        id = form.get('id')
        if not id or id != pa.get('id'):
            return True
        instance = component.getAdapter(self.object, IInstance, name='editor')
        instance.template = self.schema
        self.formState = formState = instance.applyTemplate(data=form,
                                            fieldHandlers=self.fieldHandlers)
        #formState = self.formState = self.validate(form)
        if formState.severity > 0:
            return True
        pw = form.get('password')
        pwConfirm = form.get('passwordConfirm')
        if pw != pwConfirm:
            fi = formState.fieldInstances['password']
            fi.setError('confirm_nomatch', self.formErrors)
            formState.severity = max(formState.severity, fi.severity)
            return True
        del pa['id']
        del pa['timestamp']
        ip = getInternalPrincipal(userId)
        ip.setPassword(pw)
        if self.feedbackUrl:
            self.request.response.redirect(self.feedbackUrl)
        else:
            url = '%s?loops.message=%s' % (self.url, self.message)
            self.request.response.redirect(url)
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

