"""This module contains the `EventHandler` class.

"""

class Event():
    """A generic event class that can be subclassed to make custom
    events.

    """
    
    pass

class EventHandler():
    """A simple event handler.

    """

    def __init__(self):
        """Instantiates an event handler.

        """
        self._subscribers = []  # the list of subscribers

    def subscribe(self, func):
        """Used to subscribe to the event handler.

        Args:
            func (callable): The callable object to add to the list of
                subscribers. Must take one argument.

        """
        self._subscribers.append(func)

    def unsubscribe(self, func):
        """Used to unsubscribe from the event handler.

        Args:
            func (callable): The callable object to remove from the list
                of subscribers. Must take one argument.

        """
        self._subscribers.remove(func)

    def notify(self, event):
        """Notifies the subscribers of an event. More specifically, each
        callable in the list of subscribers is called with the given
        event object as the argument.

        Args:
            event (obj): The object to pass to the subscribing
                callables.

        """
        for func in self._subscribers:
            func(event)