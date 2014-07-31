#
#  Copyright (c) 2014 Helmut Merz helmutm@cy55.de
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
loops.knowledge.qualification package.
"""

from zope import interface, component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy

from cybertools.browser.action import actions
from loops.browser.action import DialogAction
from loops.browser.concept import ConceptView
from loops.expert.browser.report import ResultsConceptView
from loops.organize.party import getPersonForUser
from loops.util import _

template = ViewPageTemplateFile('qualification_macros.pt')


actions.register('createJobPosition', 'portlet', DialogAction,
        title=_(u'Create Job...'),
        description=_(u'Create a new job / position.'),
        viewName='create_concept.html',
        dialogName='createPosition',
        typeToken='.loops/concepts/jobposition',
        fixedType=True,
        innerForm='inner_concept_form.html',
        permission='loops.AssignAsParent',
)


class Qualifications(ResultsConceptView):

    reportName = 'qualification_overview'


class QualificationBaseView(object):

    template = template
    templateName = 'knowledge.qualification'

    @Lazy
    def institutionType(self):
        return self.conceptManager['institution']

    @Lazy
    def jobPositionType(self):
        return self.conceptManager['jobposition']

    @Lazy
    def isMemberPredicate(self):
        return self.conceptManager['ismember']


class JobPositionsOverview(QualificationBaseView, ConceptView):

    macroName = 'jobpositions'

    @Lazy
    def positions(self):
        result = []
        p = getPersonForUser(self.context, self.request)
        if p is not None:
            for parent in p.getParents([self.isMemberPredicate]):
                if parent.conceptType == self.institutionType:
                    for child in parent.getChildren([self.defaultPredicate]):
                        if child.conceptType == self.jobPositionType:
                            result.append(child)
        return result


class IPSkillsForm(QualificationBaseView, ConceptView):
    """ Form for entering interpersonal skills required for a certain position.
    """

    macroName = 'ipskillsform'

