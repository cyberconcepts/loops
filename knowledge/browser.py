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
Definition of view classes and other browser related stuff for the
loops.knowledge package.
"""

from zope import interface, component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy

from cybertools.browser.action import actions
from cybertools.typology.interfaces import IType
from loops.browser.action import DialogAction
from loops.browser.common import BaseView
from loops.browser.concept import ConceptView
from loops.common import adapted
from loops.knowledge.interfaces import IPerson, ITask
from loops.organize.party import getPersonForUser
from loops.organize.personal import favorite
from loops.organize.personal.interfaces import IFavorites
from loops.security.common import checkPermission
from loops import util
from loops.util import _


template = ViewPageTemplateFile('knowledge_macros.pt')
knowledge_macros = template.macros


actions.register('createTopic', 'portlet', DialogAction,
        title=_(u'Create Topic...'),
        description=_(u'Create a new topic.'),
        viewName='create_concept.html',
        dialogName='createTopic',
        typeToken='.loops/concepts/topic',
        fixedType=True,
        innerForm='inner_concept_form.html',
        permission='loops.AssignAsParent',
)

actions.register('editTopic', 'portlet', DialogAction,
        title=_(u'Edit Topic...'),
        description=_(u'Modify topic.'),
        viewName='edit_concept.html',
        dialogName='editTopic',
        permission='zope.ManageContent',
)

actions.register('createQualification', 'portlet', DialogAction,
        title=_(u'Create Qualification Record...'),
        description=_(u'Create a qualification record for this person.'),
        viewName='create_qualification.html',
        dialogName='createQualification',
        prerequisites=['registerDojoDateWidget', 'registerDojoNumberWidget',
                       'registerDojoTextarea'],
        permission='loops.AssignAsParent',
)


class InstitutionMixin(object):

    knowledge_macros = knowledge_macros

    adminMaySelectAllInstitutions = True

    @Lazy
    def institutionType(self):
        return self.conceptManager['institution']

    @Lazy
    def institutions(self):
        if self.adminMaySelectAllInstitutions:
            if checkPermission('loops.ManageWorkspaces', self.context):
                return self.getAllInstitutions()
        result = []
        p = getPersonForUser(self.context, self.request)
        if p is None:
            return result
        for parent in p.getParents(
                [self.memberPredicate, self.masterPredicate]):
            if parent.conceptType == self.institutionType:
                result.append(dict(
                        object=adapted(parent), 
                        title=parent.title,
                        uid=util.getUidForObject(parent)))
        return result

    def getAllInstitutions(self):
        insts = self.institutionType.getChildren([self.typePredicate])
        return [dict(object=adapted(inst),
                     title=inst.title,
                     uid=util.getUidForObject(inst)) for inst in insts]

    def setInstitution(self, uid):
        inst = util.getObjectForUid(uid)
        person = getPersonForUser(self.context, self.request)
        favorite.setInstitution(person, inst)
        self.institution = inst
        return True

    def getSavedInstitution(self):
        person = getPersonForUser(self.context, self.request)
        favorites = IFavorites(self.loopsRoot.getRecordManager()['favorites'])
        for inst in favorites.list(person, type='institution'):
            return adapted(util.getObjectForUid(inst))

    @Lazy
    def institution(self):
        saved = self.getSavedInstitution()
        for inst in self.institutions:
            if inst['object'] == saved:
                return inst['object']
        if self.institutions:
            return self.institutions[0]['object']


class MyKnowledge(ConceptView):

    template = template

    @Lazy
    def macro(self):
        return self.template.macros['requirement_providers']

    @Lazy
    def person(self):
        person = getPersonForUser(self.context, self.request)
        if person is not None:
            person = IPerson(person)
        return person

    def myKnowledge(self):
        if self.person is None:
            return ()
        knowledge = self.person.getKnowledge()
        return knowledge

    def myKnowledgeProvidersForTask(self):
        if self.person is None:
            return ()
        request = self.request
        task = ITask(self.context)
        # TODO: check correct conceptType for context!
        providers = self.person.getProvidersNeeded(task)
        return ({'required': BaseView(req.context, request),
                 'providers': (BaseView(p.context, request) for p in prov)}
                    for req, prov in providers)


class Candidates(ConceptView):

    template = template

    @Lazy
    def macro(self):
        return self.template.macros['requirement_candidates']


