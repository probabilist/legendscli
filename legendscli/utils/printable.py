"""A module with tools for creating printable classes.

Any subclass of Printable will have a custom `__repr__` method that
produces a clean display of the object's attributes and values when that
object is passed to the built-in `print` function.

"""

from types import MappingProxyType
from pprint import pformat

__all__ = ['printify', 'PrintOnly', 'Printable']

def printify(obj):
    """Processes the given object and returns a new object more suitable
    for printing. No processing occurs unless the given object is one of
    these types: Printable, MappingProxyType, dict, list, or tuple.

    If the object is a Printable, it is replaced by a PrintOnly object
    using the given object's `shortName` method.

    If the object is a MappingProxyType, it is turned into a dict and
    reprintified.

    If the object is a dict, each value is recursively printified.

    If the object is a list or tuple, each item is recursively
    printified.

    Args:
        obj (obj): The object to be printified.

    Returns:
        obj: The printified object.

    """
    if isinstance(obj, Printable):
        return PrintOnly('<' + obj.shortName() + '>')
    if isinstance(obj, MappingProxyType):
        return printify(dict(obj))
    if type(obj) == type({}):
        return {k: printify(v) for k, v in obj.items()}
    if type(obj) == type([]):
        return [printify(v) for v in obj]
    if type(obj) == type(tuple()):
        return tuple(printify(v) for v in obj)
    return obj

class PrintOnly():
    """An empty object with a custom `__repr__` method for printing.

    """
    
    def __init__(self, text):
        """

        Args:
            text (str): The text to use in `__repr__`.
        """
        self._text = text

    def __repr__(self):
        """(override) Overrides the built-in `__repr__` method to use
        the custom text instead.
        """
        return self._text

class Printable():
    """An object with a customized format for printing.

    The `printify` method builds a custom dictionary out of the object's
    attributes. The custom `__repr__` method formats this dictionary
    using the pretty print package, and returns the formatted
    dictionary.

    Attributes:
        noPrint (list of str): A list of attribute names that will not
            be included when the object is printed.
        collapse (list of str): A list of attribute names whose values
            will be collapsed into a single line when printed.
        expand (list of str): A list of attribute names. If the value of
            attribute on this list if a Printable object, that Printable
            object's short name will not be used, and instead the
            Printable object will be printified.

    """

    _ignore = ['noPrint', 'collapse', 'shortName', 'expand', 'ignore']

    def __init__(self):
        self.noPrint = []
        self.collapse = []
        self.expand = []

    def shortName(self):
        """Produces a short description of the object.

        Returns:
            str: The description of the object to use when the object
                appears as a value in another Printable object.

        """
        return self.__class__.__name__ + ' object'

    def printify(self):
        """Builds a dictionary out of the calling object's attributes,
        ignoring callables, attributes beginning with '_', any
        attributes in the `noPrint` attribute, and any attributes
        in the `Printable._ignore` list.

        The values of the attributes are passed to the `printify`
        function before being added to the dictionary. If the attribute
        is in the `collapse` list, its value is replaced by a PrintOnly
        object that simply gives its class.

        If the attribute is in the `expand` list and its value is a
        Printable object, the object is not passed to the `printify`
        function. (Passing a Printable object to the `printify` function
        causes its short name to be used.) Instead, the dictionary
        returned by that object's `printify` method is used.

        Returns:
            dict: A dictionary used for printing the calling object.

        """
        D = {}
        for attrName in self.__dir__():
            if (
                attrName[0] == '_'
                or attrName in self.noPrint
                or attrName in Printable._ignore
            ):
                continue
            value = getattr(self, attrName)
            if callable(value):
                continue
            if attrName in self.collapse:
                typeName = value.__class__.__name__
                if typeName == 'mappingproxy':
                    typeName = 'dict'
                value = PrintOnly(
                    '<' + typeName + ' object>'
                )
            if attrName in self.expand and isinstance(value, Printable):
                D[attrName] = value.printify()
            else:
                D[attrName] = printify(value)
        return D

    def __repr__(self):
        """(override) Overrides the built-in `__repr__` method to first
        apply the `printify` method, and then use the pretty print
        package to produce a clean visual display.
        """
        return (
            '<' + self.shortName() + '>\n'
            + 'Attributes:\n'
            + pformat(self.printify())
        )
