from twisted.python.log import msg, err


class Logger(object):
    """
    Simple log frontend with system-component that is not based on the
    current context, but a function of the L{Logger} object.
    
    @ivar system: the system string
    @type system: C{str}
    """
    
    def __init__(self, system):
        self.system = system

    def msg(self, *args, **kw):
        kw.update({'system':self.system})
        msg(*args, **kw)

    def err(self, _stuff=None, _why=None, **kw):
        kw.update({'system':self.system})
        err(_stuff=_stuff, _why=_why, **kw)
