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
View class(es) for resource classifiers.
"""

from logging import getLogger
import transaction
from zope import interface, component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.traversing.api import getName

from loops.browser.concept import ConceptView
from loops.common import adapted

logger = getLogger('ClassifierView')


class ClassifierView(ConceptView):

    macro_template = ViewPageTemplateFile('classifier_macros.pt')

    @property
    def macro(self):
        return self.macro_template.macros['render_classifier']

    def update(self):
        if 'update' in self.request.form:
            cta = adapted(self.context)
            if cta is not None:
                for idx, r in enumerate(collectResources(self.context)):
                    if idx % 1000 == 0:
                        logger.info('Committing, resource # %s' % idx)
                        transaction.commit()
                    cta.process(r)
            logger.info('Finished processing')
            transaction.commit()
        return True


def collectResources(concept, checkedConcepts=None, result=None):
    logger.info('Start collecting resources for %s' % getName(concept))
    if result is None:
        result = []
    if checkedConcepts is None:
        checkedConcepts = []
    for r in concept.getResources():
        if r not in result:
            result.append(r)
    for c in concept.getChildren():
        if c not in checkedConcepts:
            checkedConcepts.append(c)
            collectResources(c, checkedConcepts, result)
    logger.info('Collected %s resources' % len(result))
    return result
