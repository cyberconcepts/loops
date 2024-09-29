# loops.browser.mobile.default

""" Default layouts for the loops mobile skin.
"""

from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope import component

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
