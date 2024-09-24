# loops.browser.util

""" Utilities.
"""

import re, urllib
from zope.browserpage import ViewPageTemplateFile
from zope.browsermenu.menu import BrowserMenu
from zope.browsermenu.interfaces import IBrowserSubMenuItem
from zope import component
from zope.formlib.namedtemplate import NamedTemplateImplementation


pageform = NamedTemplateImplementation(ViewPageTemplateFile('pageform.pt'))
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


pattern = re.compile(r'[ /\?\+\|%]')

def normalizeForUrl(text):
    return urllib.quote(pattern.sub('-', text).encode('UTF-8'))
