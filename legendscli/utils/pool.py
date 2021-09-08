"""Classes used to manage collections of items.

"""

from types import MappingProxyType
from legendscli.utils.printable import Printable
from legendscli.utils.eventhandler import Event, EventHandler
from legendscli.utils.functions import writeToCSV

class PoolChangeEvent(Event):
    """An event indicating the pool has changed.

    Attributes:
        pool (Pool): The pool that created the event.
        item (Item): The item involved in the change.
    """

    def __init__(self, pool, item=None, status=None):
        """Creates a pool change event with the given item and status.

        Args:
            pool (Pool): The pool that has changed.
            item (Item): The item involved in the change.
            status (str): One of 'new', 'removed', or 'changed'.

        Raises:
            ValueError: If trying to set item without also setting
                status.

        """
        if item is not None and status is None:
            raise ValueError(
                'cannot set item without also setting status'
            )
        self.pool = pool
        self.item = item
        if item:
            self.status = status

    @property
    def status(self):
        """str: If the `item` attribute is `None`, this is also `None`.
        Otherwise the status is one of 'new', 'removed', or 'changed'.

        Raises:
            AttributeError: If trying to set value when `item` attribute
                is `None`.
            ValueError: If trying to set value to something other than
                'new', 'removed', or 'changed'.

        """
        return None if self.item is None else self._status

    @status.setter
    def status(self, value):
        if self.item is None:
            raise AttributeError('cannot set status without an item')
        if value not in ['new', 'removed', 'changed']:
            raise ValueError("status must be 'new', 'removed', or 'changed'")
        self._status = value

    @property
    def multiple(self):
        """bool: True if the `item` attribute is `None`, indicating that
        there was a change to multiple items in the pool.
        """
        return self.item is None

class Pool(Printable):
    """A collection of items.

    By default, items in the pool are aware of which pool they're in,
    and may receive communications from the pool. As such, items can
    only be in one pool at a time. Subclasses can disable this by
    setting the `_blind` attribute to True. In this case, items do not
    need an `inPool` attribute or an `onPoolChange` method.

    Attributes:
        onChange (EventHandler): When the pool is modified, it uses this
            event handler to notify subscribers.

    """

    def __init__(self):
        """Creates the `Pool` object.

        """
        Printable.__init__(self)
        self._blind = False
        self._items = {}
        self.onChange = EventHandler()
        self._ignoreItemChange = False  # set to True to prevent calls
                                        # to the `onItemChange` method

    @property
    def items(self):
        """dict of int:Item: Each item has an ID number, assigned by, and
        used internally by, the pool. The `items` property is a
        dictionary mapping item IDs to items.
        """
        return MappingProxyType(self._items)

    @property
    def length(self):
        """int: The number of items in the pool."""
        return len(self._items)

    def addItem(self, item, idNum=None, safe=True):
        """Adds the given item to the pool with the given ID number. If
        an ID number is not given, one is automatically generated.

        Args:
            item (Item): The item to add to the pool.
            idNum (int): The ID number to assign to the item. Should be
                a positive integer. If not provided, one is
                automatically generated.
            safe (bool): Set to False to avoid checking for duplicates.

        Raises:
            ValueError: If given ID number is already in use.

        """
        if idNum in self._items:
            raise ValueError('ID number already in use')
        if safe and item in self._items.values():
            raise ValueError('item already in this pool')
        if not self._blind and item.inPool is not None:
            raise ValueError('item already in another pool')
        if idNum is None:
            if self.length == 0:
                idNum = 1
            else:
                idNum = max(self._items.keys()) + 1
        self._items[idNum] = item
        item.onChange.subscribe(self.onItemChange)
        if not self._blind:
            item.inPool = (self, idNum)
            self.onChange.subscribe(item.onPoolChange)

    def removeItem(self, item):
        """Unsubscribes from the given item's `onChange` event handler,
        then removes it from the pool. Fails silently if the given item
        is not in the pool.

        Args:
            item (Item): The item to remove from the pool.

        """
        if item not in self._items.values():
            return
        if not self._blind:
            self.onChange.unsubscribe(item.onPoolChange)
            item.inPool = None
        item.onChange.unsubscribe(self.onItemChange)
        del self._items[item.inPool[1]]

    def onItemChange(self, item):
        """This method is called when an item in the pool is modified.

        Args:
            item (Item): The item that has changed.

        """
        if self._ignoreItemChange:
            return
        self.onChange.notify(PoolChangeEvent(self, item, 'changed'))

class PoolViewer(Printable):
    """A tool for viewing a Pool object with spreadsheets.

    Attributes:
        filters (list of func): Each function in the filters list should
            take one dict argument and return a boolean. The argument
            should be a simplified stat dictionary like those in the
            values of the `displayStats` dictionary.

    """

    def __init__(self, pool):
        """Creates a PoolViewer object to view the given pool.
        Subscribes to the given pools's `onChange` event handler.

        Args:
            pool (Pool): The roster to associate with the viewer.

        """
        Printable.__init__(self)
        self.collapse = ['displayStats', 'filteredStats']
        self._pool = pool
        pool.onChange.subscribe(self.onPoolChange)
        self._displayStats = {}
        self.filters = []
        self.makeDisplayStats()

    @property
    def fields(self):
        """tuple of str: The stat names used in the header of
        spreadsheets created by the pool viewer.
        """
        if self._pool.length == 0:
            return None
        return tuple(next(iter(self.displayStats.values())).keys())

    @property
    def displayStats(self):
        """dict of int:dict of str:(str or int or float))): A
        dictionary mapping item IDs to their simplified stat
        dictionaries. The simplified stat dictionary maps a limited
        collection of stat names (i.e. the ones in the `fields`
        property) to their values.
        """
        return MappingProxyType(self._displayStats)

    @property
    def filteredStats(self):
        """dict of str:(dict of str:(str or int or float))): Same as
        `displayStats`, but with items filtered out. Items are checked
        by passing their simplified stat dictionaries to the functions
        in the `filters` list. If any function returns False, the item
        is filtered out.
        """
        return MappingProxyType({
            itemID: statDict
            for itemID, statDict in self._displayStats.items()
            if all(filter(statDict) for filter in self.filters)
        })

    def makeDisplayStats(self, item=None, safe=True):
        """Makes a simplified dictionary of item statistics, suitable
        for displaying in a spreadsheet, then stores it for retrieval by
        the `displayStats` property.

        Should be overriden by the subclass.

        Args:
            item (Item): Uses statistics from this item. If no item is
                provided, the method is run on every item in the
                associated pool.
            safe (bool): Set to False to skip checking for the given
                item in the associated pool.

        Raises:
            ValueError: If the given item is not in the associated pool.

        """
        if item is None:
            for item in self._pool.items.values():
                self.makeDisplayStats(item, False)
            return
        if safe and item not in self._pool.items.values():
            raise ValueError('item not in pool')
        displayStats = {}   # the subclass would replace this line with
                            # code that would build the simplified
                            # dictionary of item statistics for `item`
        self._displayStats[item.inPool[1]] = MappingProxyType(displayStats)

    def onPoolChange(self, event):
        """Updates the stored display stats when the associated pool
        changes.

        Args:
            event (PoolChangeEvent): The event sent by the associated
                pool when it changes.

        """
        if event.status == 'removed':
            del self._displayStats[event.item.inPool[1]]
        else:
            self.makeDisplayStats(event.item, False)

    def sort(self, field, reverse=False):
        """Sorts the display stats by the given field name.

        Args:
            field (str): Should match a value in the `fields` property.
            reverse (bool): Set to True to sort descending.

        """
        sortedDisplayStats = {
            itemID: statDict for itemID, statDict in sorted(
                self._displayStats.items(),
                key=lambda item:item[1][field],
                reverse=reverse
            )
        }
        self._displayStats = sortedDisplayStats

    def printCSV(self, fileName='pool'):
        """Writes the roster's display stats to a CSV file  in the
        current working directory.

        Args:
            fileName (str): The name, without extension, to give to the
                csv file.

        Raises:
            ValueError: If the associated pool is empty.

        """
        if self._pool.length == 0:
            raise ValueError('pool is empty')
        writeToCSV(self.fields, self.filteredStats.values(), fileName)

class Item(Printable):
    """An item to be collected into a Pool object.

    Attributes:
        onChange (EventHandler): When the item is modified, it uses this
            event handler to send itself to subscribers.
        inPool (tuple of Pool, int): A 2-tuple whose first value is the
            Pool object that the item is in, and whose second value is
            the ID used internally by the Pool object to identify the
            item. This attribute is set by the Pool object.

    """

    def __init__(self):
        Printable.__init__(self)
        self.onChange = EventHandler()
        self.inPool = None

    def onPoolChange(self, event):
        """This method is called when the pool that the item is in is
        modified.

        """
        pass

