#
#  Copyright (c) 2011 Helmut Merz helmutm@cy55.de
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
Utilities.

$Id$
"""

from zope.app.pagetemplate import ViewPageTemplateFile
from zope.app.publisher.browser.menu import BrowserMenu
from zope.app.publisher.interfaces.browser import IBrowserSubMenuItem
from zope import component
from zope.formlib.namedtemplate import NamedTemplateImplementation


pageform = NamedTemplateImplementation(ViewPageTemplateFile('pageform.pt'))
#dataform = NamedTemplateImplementation(ViewPageTemplateFile('dataform.pt'))
dataform = ViewPageTemplateFile('dataform.pt')

concept_macros = NamedTemplateImplementation(ViewPageTemplateFile('concept_macros.pt'))
node_macros = NamedTemplateImplementation(ViewPageTemplateFile('node_macros.pt'))


class LoopsMenu(BrowserMenu):
    """ Use this class in zope/app/menus.zcml for zmi_views for
        getting a different order of menu items.
    """

    def getMenuItems(self, object, request):
        """Return menu item entries in a TAL-friendly form."""
        result = sorted([(item.order, item.action.lower(), item)
                    for name, item in component.getAdapters(
                            (object, request), self.getMenuItemType())
                    if item.available()])
        return [
            {'title': item.title,
             'description': item.description,
             'action': item.action,
             'selected': (item.selected() and u'selected') or u'',
             'icon': item.icon,
             'extra': item.extra,
             'submenu': (IBrowserSubMenuItem.providedBy(item) and
                         getMenu(item.submenuId, object, request)) or None}
            for order, action, item in result]


def html_quote(text, character_entities=((u'&', u'&amp;'), (u'<', u'&lt;' ),
                                         (u'>', u'&gt;' ), (u'"', u'&quot;'))):
    for re, name in character_entities:
        text = text.replace(re, name)
    return text
