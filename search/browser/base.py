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
Definition of basic view classes and other browser related stuff for the
loops.search package.

$Id$
"""

from zope import interface, component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.formlib.namedtemplate import NamedTemplate, NamedTemplateImplementation
from zope.i18nmessageid import MessageFactory

from loops.browser.common import BaseView

_ = MessageFactory('zope')


search_macros = NamedTemplateImplementation(
                    ViewPageTemplateFile('search.pt'))


class Search(BaseView):

    template = NamedTemplate('loops.search_macros')

    @Lazy
    def macro(self):
        return self.template.macros['search']

