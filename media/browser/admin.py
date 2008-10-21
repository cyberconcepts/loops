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
View for regenerating all transformed media assets.

Authors: Johann Schimpf, Erich Seifert.

$Id$
"""

from logging import getLogger
import traceback
from zope import component

from cybertools.media.interfaces import IMediaAsset


class RegenerationView(object):

    def __call__(self):
        conceptType = self.request.get('type')
        if not conceptType:
            return '*** No type given!'
        tMediaAsset = self.context.getLoopsRoot().getConceptManager()[conceptType]
        # Remove old transformed versions
        #storageDir = assetManager.options.get("storage_parameters")
        # Regenerate all media asset transforations
        resources = tMediaAsset.getResources()
        logger = getLogger('Asset Manager')
        errors = 0
        for res in resources:
            asset = component.queryAdapter(res, IMediaAsset)
            if asset != None and res.contentType.startswith('image/'):
                logger.info('*** regenerating: ' + res.__name__)
                try:
                    asset.transform()
                except:
                    logger.warn(traceback.format_exc())
                    errors += 1
        if errors:
            return 'Done - there were %i errors.' % errors
        return 'Done.'
