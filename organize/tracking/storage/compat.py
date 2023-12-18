# loops.organize.tracking.storage.compat

"""loops compatibility layer on cco.storage.tracking.

Provides a Container subclass that defines methods from cybertools...TrackingStorage
used by code based on loops.organize.tracking.
"""

from cco.storage.tracking import record


class Container(record.Container):

    pass
