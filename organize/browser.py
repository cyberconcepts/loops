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
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.app.principalannotation import annotations
from zope.cachedescriptors.property import Lazy
from zope.i18nmessageid import MessageFactory

from loops.browser.common import BaseView
from loops.browser.concept import ConceptRelationView
from loops.organize.interfaces import ANNOTATION_KEY, IMemberRegistrationManager
from loops.organize.interfaces import raiseValidationError

_ = MessageFactory('zope')


class MyConcepts(BaseView):

    template = ViewPageTemplateFile('../browser/concept_macros.pt')
    macro = template.macros['conceptlisting']

    def __init__(self, context, request):
        self.context = context
        self.request = request
        pa = annotations(request.principal)
        self.person = pa.get(ANNOTATION_KEY, None)
        if self.person is not None:
            self.context = self.person

    def children(self):
        if self.person is None:
            return
        for r in self.person.getChildRelations():
            yield ConceptRelationView(r, self.request, contextIsSecond=True)

    def parents(self):
        if self.person is None:
            return
        for r in self.person.getParentRelations():
            yield ConceptRelationView(r, self.request)

    def resources(self):
        if self.person is None:
            return
        for r in self.person.getResourceRelations():
            yield ConceptRelationView(r, self.request, contextIsSecond=True)


class MemberRegistration(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def register(self):
        form = self.request.form
        pw = form.get('field.passwd')
        if form.get('field.passwdConfirm') != pw:
            raiseValidationError(_(u'Password and password confirmation '
                                    'do not match.'))
        regMan = IMemberRegistrationManager(self.context.getLoopsRoot())
        person = regMan.register(form.get('field.userId'), pw,
                                 form.get('field.lastName'),
                                 form.get('field.firstName'))
        return person

