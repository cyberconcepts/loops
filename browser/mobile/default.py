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
Default layouts for the loops mobile skin.

$Id$
"""

from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope import component
from zope.interface import implements

from cybertools.browser.renderer import RendererFactory
from cybertools.composer.layout.base import Layout
from cybertools.composer.layout.browser.standard import standardRenderers


defaultRenderers = RendererFactory(ViewPageTemplateFile('default.pt'))


Layout('page.loops.mobile', 'page', renderer=standardRenderers.page,
       sublayouts=set(['body.loops.mobile']),
       favicon='favicon.png')

Layout('body.loops.mobile', 'page.body', renderer=defaultRenderers.body,
       sublayouts=set(['center.loops.mobile']))

Layout('center.loops.mobile', 'body.center', renderer=defaultRenderers.center,
       instanceName='target', sublayouts=[],
       defaultSublayout='notfound.loops')

Layout('homepage.loops.mobile', 'center.content', renderer=defaultRenderers.homepage,
       instanceName='target')

Layout('notfound.loops', 'center.content', renderer=defaultRenderers.notfound)
