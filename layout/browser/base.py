#
#  Copyright (c) 2009 Helmut Merz helmutm@cy55.de
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
Base classes for layout-based views.

$Id$
"""

import re

from zope import component
from zope.cachedescriptors.property import Lazy
from zope.proxy import removeAllProxies
from zope.traversing.browser import absoluteURL

from loops.common import adapted
from loops.i18n.browser import LanguageInfo
from loops import util


class BaseView(object):

    def __init__(self, context, request):
        self.context = context  # this is the adapted concept!
        self.request = request

    @Lazy
    def title(self):
        return self.context.title

    @Lazy
    def description(self):
        return self.context.description

    @Lazy
    def uid(self):
        return util.getUidForObject(self.context.context)

    @Lazy
    def menu(self):
        return self.node.getMenu()

    @Lazy
    def url(self):
        return '%s/.%s-%s' % (absoluteURL(self.menu, self.request),
                              self.context.uid, normalize(self.context.title))

    def requireDojo(self, *packages):
        # TODO: make sure dojo and dojo_require are displayed in page.js
        djInfo = self.request.annotations.setdefault('ajax.dojo', {})
        requirements = djInfo.setdefault('requirements', set())
        for p in packages:
            requirements.add(p)

    def renderText(self, text, contentType):
        typeKey = util.renderingFactories.get(contentType, None)
        if typeKey is None:
            if contentType == u'text/html':
                return util.toUnicode(text)
            return u'<pre>%s</pre>' % util.html_quote(util.toUnicode(text))
        source = component.createObject(typeKey, text)
        view = component.getMultiAdapter((removeAllProxies(source), self.request))
        return view.render()


pattern = re.compile(r'[ /\?\+%]')

def normalize(text):
    return pattern.sub('-', text)