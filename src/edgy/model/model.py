from edgy.model.attributes import _Attribute, Integer, Sequence, String, Boolean


class ModelError(Exception):
    pass


class Model(object):
    """
    Base class for all model objects.
    """

    class __metaclass__(type):
        """
        Simple metaclass that is responsible for making sure that all
        model attributes has a proper name.
        """
        def __init__(cls, name, bases, dict):
            for name, attribute in dict.iteritems():
                if name[0] != '_' and isinstance(attribute, _Attribute):
                    if attribute.name is None:
                        attribute.name = name
            type.__init__(cls, name, bases, dict)

    def __init__(self, _do_not_finalize=False, **kw):
        """
        Initialize model objects with initial values provided in
        C{kw}.

        If C{_do_not_finalize} is C{True} then the instance will not
        be finalized and non-optional attributes will not be enforced.
        """
        self._attributes = {}
        for k, v in kw.iteritems():
            setattr(self, k, v)
        if not _do_not_finalize:
            self._finalize()

    def _finalize(self):
        """
        Finalize model object instance; verify that all attributes is
        in place that must be there.
        """
        for attribute in getAttributes(self.__class__):
            try:
                getattr(self, attribute.name)
            except AttributeError, e:
                if attribute.optional is False:
                    raise ModelError('attribute %s is missing' % (
                            attribute.name))
        # done!

    def __str__(self):
        """
        Return a string that somewhat represents the content of this
        model object.
        """
        attr_strs = []
        for attribute in getAttributes(self.__class__):
            try:
                attr_strs.append('%s=%r' % (attribute.name,
                    getattr(self, attribute.name)))
            except AttributeError:
                continue
        return '<%s %s>' % (self.__class__.__name__, ', '.join(attr_strs))

    __repr__ = __str__


def getAttributes(modelClass, recurse=True):
    """
    Generate a sequence of attributes for all attributes of the
    C{modelClass}.
    """
    def _cls(cls):
        for name, attribute in cls.__dict__.iteritems():
            if isinstance(attribute, _Attribute):
                yield attribute
        if recurse:
            for basecls in cls.__bases__:
                for attribute in _cls(basecls):
                    yield attribute
    return _cls(modelClass)


def getNamedAttributes(modelClass, recurse=True):    
    def _cls(cls):
        for name, attribute in cls.__dict__.iteritems():
            if isinstance(attribute, _Attribute):
                yield name, attribute
        if recurse:
            for basecls in cls.__bases__:
                for name, attribute in _cls(basecls):
                    yield name, attribute
    return _cls(modelClass)
