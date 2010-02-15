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
view class(es) for import/export.

$Id$
"""

from cStringIO import StringIO
from logging import getLogger
import os
import time
from zope import component
from zope.interface import Interface, implements
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.traversing.api import getName, getPath

from cybertools.browser.form import FormController
from cybertools.util.date import str2timeStamp, formatTimeStamp
from loops.browser.common import BaseView
from loops.browser.concept import ConceptView
from loops.external.base import Extractor
from loops.external.interfaces import IWriter
from loops import util


control_macros = ViewPageTemplateFile('control.pt')


class SyncChanges(ConceptView):
    """ View for controlling the transfer of changes from a loops site
        to another one.
    """

    @Lazy
    def macro(self):
        return control_macros.macros['main']

    @Lazy
    def changed(self):
        return (self.request.get('changed_since') or
                formatTimeStamp(self.lastSyncTimeStamp))

    @Lazy
    def lastSyncTime(self):
        if self.lastSyncTimeStamp is None:
            return u'-'
        return formatTimeStamp(self.lastSyncTimeStamp)

    @Lazy
    def lastSyncTimeStamp(self):
        return None


class ChangesSave(FormController):

    @Lazy
    def baseDirectory(self):
        return util.getVarDirectory(self.request)

    @Lazy
    def sitePath(self):
        return getPath(self.view.loopsRoot)[1:].replace('/', '_')

    @Lazy
    def exportDirectory(self):
        directory = os.path.join(self.baseDirectory, 'export',
                                 '_'.join((self.sitePath,
                                           getName(self.targetView.context))))
        if not os.path.exists(directory):
            os.makedirs(directory)
        return directory

    @Lazy
    def targetView(self):
        return self.view.virtualTarget

    @Lazy
    def types(self):
        typeIds = self.targetView.options('types')
        return [self.view.conceptManager[t] for t in typeIds]

    @Lazy
    def changed(self):
        since = self.request.get('changed_since')
        return since and str2timeStamp(since) or self.targetView.lastSyncTimeStamp

    @Lazy
    def transcript(self):
        return StringIO()

    def update(self):
        self.export()
        return True

    def export(self):
        self.clearExportDirectory()
        extractor = Extractor(self.view.loopsRoot, self.exportDirectory)
        elements = extractor.extractChanges(self.changed, self.types)
        writer = component.getUtility(IWriter)
        f = open(os.path.join(self.exportDirectory, '_changes.dmp'), 'w')
        writer.write(elements, f)
        f.close()

    def clearExportDirectory(self):
        for fn in os.listdir(self.exportDirectory):
            os.unlink(os.path.join(self.exportDirectory, fn))


class ChangesSync(ChangesSave):

    def update(self):
        self.export()
        self.transfer()
        self.triggerImport()
        #self.recordExecution()
        return True

    def transfer(self):
        targetPath = self.targetView.options('target')[0]
        cmd = os.popen('scp -r %s %s' % (self.exportDirectory, targetPath))
        info = cmd.read()
        result = cmd.close()
        if result:
            message = '*** scp output: %s, return code: %s' % (info, result)
            log = getLogger('loops.system.sync')
            log.warn(message)
            self.transcript.write(message + '\n')

    def triggerImport(self):
        pass

    def recordExecution(self):
        jobs = self.view.loopsRoot.getRecordManager()['jobs']
        jobs.saveUserTrack()


class SyncImport(BaseView):

    def importData(self):
        pass
