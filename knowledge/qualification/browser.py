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
loops.knowledge.qualification package.
"""

from zope import interface, component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy

from loops.browser.concept import ConceptView
from loops.expert.browser.export import ResultsConceptCSVExport
from loops.expert.browser.report import ResultsConceptView
from loops.organize.party import getPersonForUser
from loops.util import _


class Qualifications(ResultsConceptView):

    # obsolete because we can directly use ResultsConceptView

    #reportName = 'qualification_overview'

    pass    # report assigned to query via hasReport relation

