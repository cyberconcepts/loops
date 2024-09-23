#
#  Copyright (c) 2010 Helmut Merz helmutm@cy55.de
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
Configurator user interface.

$Id$
"""

from zope import component
from zope.cachedescriptors.property import Lazy
from zope.app.pagetemplate import ViewPageTemplateFile

from cybertools.meta.element import Element
from cybertools.meta.interfaces import IOptions
from loops.browser.concept import ConceptView
from loops import util


config_macros = ViewPageTemplateFile('view_macros.pt')



class ConfiguratorView(ConceptView):

    @Lazy
    def macro(self):
        return config_macros.macros['config']

    def getLoopsOptions(self):
        result = []
        data = {}
        options = IOptions(self.loopsRoot)
        options.loadContextOptions()
        #print '***', options
        for k, v in options.items():
            if k not in options.builtins:
                if isinstance(v, Element):
                    v = v.items()
                result.append(dict(name=k, value=str(v)))
        return sorted(result)

