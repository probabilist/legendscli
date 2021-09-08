"""Generic coding structures needed in the `legendscli` package.

Namespaces:
    utils

Aliases:
    utils.[function]        = utils.functions.[function]
    utils.printify          = utils.printable.printify
    utils.Printable         = utils.printable.Printable
    utils.PrintOnly         = utils.printable.PrintOnly
    utils.Event             = utils.eventhandler.Event
    utils.EventHandler      = utils.eventhandler.EventHandler
    utils.Item              = utils.pool.Item
    utils.Pool              = utils.pool.Pool
    utils.PoolChangeEvent   = utils.pool.PoolChangeEvent
    utils.PoolViewer        = utils.pool.PoolViewer

"""

from legendscli.utils.functions import *
from legendscli.utils.printable import *
from legendscli.utils.eventhandler import *
from legendscli.utils.pool import *
