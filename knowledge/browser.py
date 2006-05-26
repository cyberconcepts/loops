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
loops.knowledge package.

$Id$
"""

from zope import interface, component
from zope.app import zapi
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.formlib.namedtemplate import NamedTemplate
from zope.i18nmessageid import MessageFactory

from cybertools.typology.interfaces import IType
from loops.browser.common import BaseView
from loops.knowledge.interfaces import IPerson, ITask
from loops.organize.browser import getPersonForLoggedInUser

_ = MessageFactory('zope')


class MyKnowledge(BaseView):

    def __init__(self, context, request):
        self.context = context
        self.request = request
        person = getPersonForLoggedInUser(request)
        if person is not None:
            person = IPerson(person)
        self.person = person

    def myKnowledge(self):
        if self.person is None:
            return ()
        knowledge = self.person.getKnowledge()
        return knowledge

    def myKnowledgeProvidersForTask(self):
        if self.person is None:
            return ()
        task = ITask(self.context)
        # TODO: check correct conceptType for context!
        providers = self.person.getProvidersNeeded(task)
        return providers

