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
from urllib import urlopen, urlencode
from zope import component
from zope.interface import Interface, implements
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.traversing.api import getName, getPath

from cybertools.browser.form import FormController
from cybertools.util.date import str2timeStamp, formatTimeStamp
from loops.browser.common import BaseView
from loops.browser.concept import ConceptView
from loops.external.base import Extractor, Loader
from loops.external.interfaces import IReader, IWriter
from loops.system.job import JobRecords
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
        jobs = JobRecords(self.view.loopsRoot)
        rec = jobs.getLastRecordFor(self.nodeView.virtualTargetObject)
        if rec is not None:
            return rec.timeStamp
        return None


class ChangesSave(FormController):

    @Lazy
    def baseDirectory(self):
        return util.getVarDirectory(self.request)

    @Lazy
    def sitePath(self):
        return getPath(self.view.loopsRoot)[1:].replace('/', '_')

    @Lazy
    def subDirectory(self):
        return '_'.join((self.sitePath, getName(self.targetView.context)))

    @Lazy
    def exportDirectory(self):
        directory = os.path.join(self.baseDirectory, 'export', self.subDirectory)
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

    state = 'ok'

    @Lazy
    def targetPath(self):
        return self.targetView.options('target_dir')[0]

    def update(self):
        self.export()
        self.transfer()
        self.triggerImport()
        self.recordExecution()
        return True

    def transfer(self):
        cmd = os.popen('scp -r %s %s' % (self.exportDirectory, self.targetPath))
        info = cmd.read()
        result = cmd.close()
        if result:
            message = '*** scp output: %s, return code: %s' % (info, result)
            log = getLogger('loops.system.sync')
            log.warn(message)
            self.transcript.write(message + '\n')

    def triggerImport(self):
        targetUrl = self.targetView.options('target_url')[0]
        p = self.targetPath.split(':', 1)
        if len(p) > 1:
            path = p[1]
        else:
            path = p[0]
        path = os.path.join(path, self.subDirectory)
        f = urlopen(targetUrl, data=urlencode(dict(path=path)))
        result = f.read()
        self.transcript.write('trigger import: %s\n' % result)
        return result

    def recordExecution(self):
        jobs = JobRecords(self.view.loopsRoot)
        jobs.recordExecution(self.view.virtualTargetObject,
                             self.state, self.transcript.getvalue())


class SyncImport(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def importData(self):
        path = self.request.get('path', '???')
        f = open(os.path.join(path, '_changes.dmp'))
        data = f.read()
        f.close()
        reader = component.getUtility(IReader)
        elements = reader.read(data)
        loader = Loader(self.context, path)
        loader.load(elements)
        return loader.logger.getvalue() + '\n' + loader.transcript.getvalue()
        return 'Done'
