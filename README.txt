loops - Linked Objects for Organizational Process Services
==========================================================

  ($Id$)

Tasks and Subtasks
~~~~~~~~~~~~~~~~~~

Let's start with creating a few example tasks:

    >>> from loops.task import Task
    >>> t1 = Task()
    >>> t1.title
    u''

    >>> t2 = Task(u't2', u'Second Task')
    >>> t2.title
    u'Second Task'

Now we want to make the second task a subtask of the first one.

In order to do this we first have to provide a relations registry. For
testing we use a simple dummy implementation.

    >>> from cybertools.relation.interfaces import IRelationsRegistry
    >>> from cybertools.relation.registry import DummyRelationsRegistry
    >>> from zope.app.testing import ztapi
    
    >>> ztapi.provideUtility(IRelationsRegistry, DummyRelationsRegistry())

Now we can assign the task t2 as a subtask to t1:
        
    >>> t1.assignSubtask(t2)

We can now ask our tasks for their subtasks and parent tasks:

    >>> st1 = t1.getSubtasks()
    >>> len(st1)
    1
    >>> t2 in st1
    True
    >>> len(t1.getParentTasks())
    0
        
    >>> pt2 = t2.getParentTasks()
    >>> len(pt2)
    1
    >>> t1 in pt2
    True
    >>> len(t2.getSubtasks())
    0
    