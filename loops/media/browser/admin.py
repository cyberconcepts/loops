# loops.media.browser.admin

""" View for regenerating all transformed media assets.

Authors: Johann Schimpf, Erich Seifert.
"""

from logging import getLogger
import traceback
from zope import component
from zope.security.proxy import removeSecurityProxy

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


class ChangeSubdirectories(object):

    search = '/home/Zope3/ctt'
    replace = '/home/33zope/ctt'

    def __call__(self):
        found = changed = 0
        context = removeSecurityProxy(self.context)
        ma = context['concepts']['media_asset']
        for obj in ma.getResources():
            found += 1
            sp = obj._storageParams
            subdir = sp.get('subdirectory', '')
            print(subdir)
            if self.search in subdir:
                changed += 1
                sp['subdirectory'] = subdir.replace(self.search, self.replace)
                obj._storageParams = sp
        return 'Done, %i media asset objects found, %i changed' % (found, changed)
