#
#  Copyright (c) 2007 Helmut Merz helmutm@cy55.de
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
View class(es) for intergrating external objects.

$Id$
"""

from zope import interface, component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy

from cybertools.typology.interfaces import IType
from loops.browser.concept import ConceptView


class ExternalCollectionView(ConceptView):

    macro_template = ViewPageTemplateFile('collection_macros.pt')

    @property
    def macro(self):
        return self.macro_template.macros['render_collection']

    def update(self):
        if 'update' in self.request.form:
            ti = IType(self.context).typeInterface
            if ti is not None:
                adapted = ti(self.context)
                adapted.update()
        return True
