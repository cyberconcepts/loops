#
#  Copyright (c) 2008 Helmut Merz helmutm@cy55.de
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
Views for displaying media assets.

Authors: Johann Schimpf, Erich Seifert.

$Id$
"""

from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.security.interfaces import Unauthorized

from loops.browser.node import NodeView
from loops.browser.resource import ResourceView, resource_macros
from loops.common import adapted
from loops import util

template = ViewPageTemplateFile('asset.pt')


class MediaAssetView(ResourceView):

    @Lazy
    def macro(self):
        #return template.macros['asset']
        if 'image/' in self.context.contentType:
            return template.macros['asset']
        else:
            return resource_macros.macros['download']

    def show(self, useAttachment=False):
        versionId = self.request.get('v')
        obj = self.adapted
        data = obj.getData(versionId)
        if not self.hasImagePermission(data):
            raise Unauthorized(str(self.contextInfo))
        contentType = obj.getContentType(versionId)
        response = self.request.response
        response.setHeader('Content-Type', contentType)
        response.setHeader('Content-Length', len(data))
        #if useAttachment or (
        #   not contentType.startswith('image/') and contentType != 'application/pdf'):
        if useAttachment:
            filename = obj.localFilename or getName(self.context)
            #filename = urllib.quote(filename)
            filename = NameChooser(getParent(self.context)).normalizeName(filename)
            response.setHeader('Content-Disposition',
                               'attachment; filename=%s' % filename)
        return data

    def hasImagePermission(self, data):
        if not 'image/' in self.context.contentType:
            return True
        if not self.isAnonymous:
            # TODO: replace with real permission (loops.ViewRestrictedMedia) check
            return True
        maxSize = self.typeOptions('media.unauthorized_max_size')
        if maxSize:
            (w, h) = self.adapted.getImageSize(data=data)
            if w > int(maxSize[0]):
                return False
            if len(maxSize) > 1 and h > int(maxSize[1]):
                return False
        return True


class MediaAssetNodeView(NodeView):

    def show(self):
        return self.targetView('mediaasset.html')
