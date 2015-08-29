#
#  Copyright (c) 2015 Helmut Merz helmutm@cy55.de
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
Definition of view classes and other browser related stuff (e.g. actions) for
loops.organize.party.
"""

from email.MIMEText import MIMEText
from zope import interface, component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.dublincore.interfaces import IZopeDublinCore
from zope.sendmail.interfaces import IMailDelivery

from cybertools.ajax import innerHtml
from cybertools.browser.action import actions
from cybertools.browser.form import FormController
from loops.browser.action import DialogAction
from loops.browser.form import EditConceptForm
from loops.browser.node import NodeView
from loops.common import adapted
from loops.organize.party import getPersonForUser
from loops.util import _

organize_macros = ViewPageTemplateFile('view_macros.pt')


actions.register('createPerson', 'portlet', DialogAction,
        title=_(u'Create Person...'),
        description=_(u'Create a new person.'),
        viewName='create_concept.html',
        dialogName='createPerson',
        typeToken='.loops/concepts/person',
        fixedType=True,
        innerForm='inner_concept_form.html',
        prerequisites=['registerDojoDateWidget'],
)

actions.register('editPerson', 'portlet', DialogAction,
        title=_(u'Edit Person...'),
        description=_(u'Modify person.'),
        viewName='edit_person.html',
        dialogName='editPerson',
        prerequisites=['registerDojoDateWidget'],
)

actions.register('createAddress', 'portlet', DialogAction,
        title=_(u'Create Address...'),
        description=_(u'Create a new address.'),
        viewName='create_concept.html',
        dialogName='createAddress',
        typeToken='.loops/concepts/address',
        fixedType=True,
        innerForm='inner_concept_form.html',
)

actions.register('editAddress', 'portlet', DialogAction,
        title=_(u'Edit Address...'),
        description=_(u'Modify address.'),
        viewName='edit_concept.html',
        dialogName='editAddress',
)

actions.register('createInstitution', 'portlet', DialogAction,
        title=_(u'Create Institution...'),
        description=_(u'Create a new institution.'),
        viewName='create_concept.html',
        dialogName='createInstitution',
        typeToken='.loops/concepts/institution',
        fixedType=True,
        innerForm='inner_concept_form.html',
)

actions.register('editInstitution', 'portlet', DialogAction,
        title=_(u'Edit Institution...'),
        description=_(u'Modify institution.'),
        viewName='edit_concept.html',
        dialogName='editInstitution',
)

actions.register('createOrgUnit', 'portlet', DialogAction,
        title=_(u'Create Orgunit...'),
        description=_(u'Create a new organizational unit.'),
        viewName='create_concept.html',
        dialogName='createOrgUnit',
        typeToken='.loops/concepts/orgunit',
        fixedType=True,
        innerForm='inner_concept_form.html',
)

actions.register('send_email', 'object', DialogAction,
        description=_(u'Send a link to this object by email.'),
        viewName='object_send_email.html',
        dialogName='',
        icon='cybertools.icons/email.png',
        cssClass='icon-action',
        prerequisites=['registerDojoTextWidget', 'registerDojoTextarea'],
        addParams=dict(version='this'),
)


class EditPersonForm(EditConceptForm):

    @Lazy
    def presetTypesForAssignment(self):
        types = list(self.typeManager.listTypes(include=('workspace',)))
        #assigned = [r.context for r in self.assignments]
        #types = [t for t in types if t.typeProvider not in assigned]
        predicates = [n for n in ['standard', 'ismember', 'ismaster', 'isowner']
                        if n in self.conceptManager]
        return [dict(title=t.title, token=t.tokenForSearch, predicates=predicates)
                        for t in types]



class SendEmailForm(NodeView):

    __call__ = innerHtml

    def checkPermissions(self):
        return (not self.isAnonymous and 
                super(SendEmailForm, self).checkPermissions())

    @property
    def macro(self):
        return organize_macros.macros['send_email']

    @Lazy
    def dialog_name(self):
        return self.request.get('dialog', 'object_send_email')

    @Lazy
    def title(self):
        return self.target.title

    @Lazy
    def targetUrl(self):
        return self.getUrlForTarget(self.virtualTargetObject)

    @Lazy
    def members(self):
        persons = self.conceptManager['person'].getChildren([self.typePredicate])
        persons = [adapted(p) for p in persons]
        # TODO: check if user has access to target
        #       see zope.app.securitypolicy.zopepolicy.settingsForObject
        return [dict(title=p.title, email=p.email, object=p)
                    for p in persons if p.email]

    @Lazy
    def membersByGroups(self):
        groups = {}
        pdata = self.members
        # TODO: see security.audit.PersonWorkSpaceAssignments
        return sorted([])

    @Lazy
    def mailBody(self):
        return '\n\n%s\n%s\n\n' % (self.title, self.targetUrl)

    @Lazy
    def subject(self):
        menu = self.context.getMenu()
        zdc = IZopeDublinCore(menu)
        zdc.languageInfo = self.languageInfo
        site = zdc.title or menu.title
        return _(u"loops Notification from '$site'",
                 mapping=dict(site=site))


class SendEmail(FormController):

    def checkPermissions(self):
        return (not self.isAnonymous and 
                super(SendEmail, self).checkPermissions())

    def update(self):
        form = self.request.form
        subject = form.get('subject') or u''
        message = form.get('mailbody') or u''
        recipients = form.get('recipients') or []
        recipients += (form.get('addrecipients') or u'').split('\n')
        # TODO: remove duplicates
        person = getPersonForUser(self.context, self.request)
        sender = person and adapted(person).email or 'loops@unknown.com'
        msg = MIMEText(message.encode('utf-8'), 'plain', 'utf-8')
        msg['Subject'] = subject.encode('utf-8')
        msg['From'] = sender
        msg['To'] = ', '.join(r.strip() for r in recipients if r.strip())
        mailhost = component.getUtility(IMailDelivery, 'Mail')
        mailhost.send(sender, recipients, msg.as_string())
        return True
