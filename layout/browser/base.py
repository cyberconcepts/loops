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

from zope.app.security.interfaces import IUnauthenticatedPrincipal
from zope import component
from zope.cachedescriptors.property import Lazy
from zope.proxy import removeAllProxies
from zope.security.proxy import removeSecurityProxy
from zope.traversing.browser import absoluteURL

from cybertools.util import format
from loops.common import adapted
from loops.i18n.browser import LanguageInfo
from loops import util


class BaseView(object):

    def __init__(self, context, request):
        self.context = removeSecurityProxy(context)  # this is the adapted concept!
        self.request = request

    @Lazy
    def loopsRoot(self):
        return self.context.getLoopsRoot()

    @Lazy
    def conceptManager(self):
        return self.loopsRoot.getConceptManager()

    @Lazy
    def resourceManager(self):
        return self.loopsRoot.getResourceManager()

    @Lazy
    def defaultPredicate(self):
        return self.conceptManager.getDefaultPredicate()

    @Lazy
    def viewAnnotations(self):
        return self.request.annotations.setdefault('loops.view', {})

    @Lazy
    def virtualTarget(self):
        return self.viewAnnotations.get('target')

    @Lazy
    def virtualTargetView(self):
        return self.viewAnnotations.get('targetView')

    @Lazy
    def node(self):
        return self.viewAnnotations.get('node')

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

    def breadcrumbs(self):
        return []
        result = [dict(label=self.title, url=self.url)]
        pageName = self.viewAnnotations.get('pageName')
        if pageName:
            result.append(dict(label=pageName.split('.')[0].title(),
                               url='%s/%s' % (self.url, pageName)))
        return result

    @Lazy
    def filter(self):
        fname = self.request.form.get('filter')
        if fname is None:
            li = getattr(self, 'layoutInstance', None)
            if li is not None:
                fname = getattr(li.template, 'filter', '')
                self.request.form['filter'] = fname
        return fname

    @Lazy
    def authenticated(self):
        return not IUnauthenticatedPrincipal.providedBy(self.request.principal)

    def requireDojo(self, *packages):
        # TODO: make sure dojo and dojo_require are displayed in page.js
        djInfo = self.request.annotations.setdefault('ajax.dojo', {})
        requirements = djInfo.setdefault('requirements', set())
        for p in packages:
            requirements.add(p)

    def getMessage(self, id):
        return self.request.form.get('loops.messages', {}).get(id, {})

    def renderText(self, text, contentType):
        typeKey = util.renderingFactories.get(contentType, None)
        if typeKey is None:
            if contentType == u'text/html':
                return util.toUnicode(text)
            return u'<pre>%s</pre>' % util.html_quote(util.toUnicode(text))
        source = component.createObject(typeKey, text)
        view = component.getMultiAdapter((removeAllProxies(source), self.request))
        return view.render()

    def nl2br(self, text):
        return format.nl2br(text)

    def getUidForObject(self, obj):
        return util.getUidForObject(obj)


pattern = re.compile(r'[ /\?\+%]')

def normalize(text):
    return pattern.sub('-', text)
