from datetime import datetime


NODEFAULT = u'edgy.model.attributes.NODEFALT'


class TypeError(Exception):
    pass


class Condition(object):

    def __init__(self, attribute, operator, value):
        self.attribite = attribute
        self.operator = operator
        self.value = value


class _Attribute(object):
    
    def __init__(self, optional=False, default=NODEFAULT, 
                 allowNone=False, name=None):
        self.optional = optional
        self.default = default
        self.name = name
        self.allowNone = allowNone

    def checkType(self, obj):
        raise NotImplementedError("checkType")

    def __get__(self, obj, cls):
        """
        Retreive value of the attribute from object C{obj}.
        
        """
        if obj is None:
            return self
        objinfo = obj._attributes
        if not self.name in objinfo:
            if self.default is not NODEFAULT:
                return self.default
            raise AttributeError(self.name)
        return objinfo[self.name]

    def __set__(self, obj, value):
        """
        Set value.
        """
        if not self.allowNone and value is None:
            raise TypeError('%s must not be None' % self.name)
        if value is not None:
            if not self.checkType(value):
                raise TypeError('%s must not be %r' % (self.name,
                        type(value)))
        objinfo = obj._attributes
        objinfo[self.name] = value

    def __lt__(self, other):
        return Condition(self, '<', other)

    def __le__(self, other):
        return Condition(self, '<=', other)

    def __eq__(self, other):
        return Condition(self, '==', other)

    def __ne__(self, other):
        return Condition(self, '!=', other)

    def __gt__(self, other):
        return Condition(self, '>', other)

    def __ge__(self, other):
        return Condition(self, '>=', other)


class Integer(_Attribute):

    @classmethod
    def checkType(cs, value):
        return type(value) in (int, long)


class String(_Attribute):
    # FIXME: should we only support unicode strings here?  feels a bit
    # more future safe.

    @classmethod
    def checkType(cls, value):
        return type(value) in (str, unicode)


class Double(_Attribute):

    @classmethod
    def checkType(cls, value):
        return type(value) == float


class Timestamp(_Attribute):

    @classmethod
    def checkType(cls, value):
        return isinstance(value, datetime)


class Boolean(_Attribute):

    @classmethod
    def checkType(cls, value):
        return value is True or value is False


class type_safe_list(object):

    def __init__(self, attribute, *elements):
        self.attribute = attribute
        self.list = list()
        for element in elements:
            self.append(element)

    def _checkType(self, element):
        if issubclass(self.attribute.elementType, _Attribute):
            if not self.attribute.elementType.checkType(element):
                raise TypeError()
        elif not isinstance(element, self.attribute.elementType):
            raise TypeError()

    def append(self, element):
        self._checkType(element)
        self.list.append(element)
    
    def extend(self, elements):
        for element in elements:
            self.append(element)
        
    def remove(self, element):
        self.list.remove(element)

    def __contains__(self, element):
        return self.list.__contains__(element)

    def __repr__(self):
        return repr(self.list) # '<type_safe_list: %r>' % self.list

    def __len__(self):
        return len(self.list)

    def __iter__(self):
        return iter(self.list)

    def __getitem__(self, item):
        return self.list[item]

    __str__ = __repr__

    # FIXME: the rest

class Reference(_Attribute):

    def __init__(self, referenceType, optional=False, allowNone=True):
        _Attribute.__init__(self, optional=optional, allowNone=allowNone,
                            default=None)
        self.referenceType = referenceType

    def checkType(self, value):
        return isinstance(value, self.referenceType)


class Sequence(_Attribute):

    def __init__(self, elementType, optional=False, allowNone=False):
        # FIXME: must verify that elementType is a model object class
        # of a primary type.
        _Attribute.__init__(self, optional=optional, allowNone=allowNone,
                            default=None)
        self.elementType = elementType

    @classmethod
    def checkType(cls, value):
        return (type(value) == list 
                or isinstance(value, type_safe_list))

    def __set__(self, obj, value):
        if not self.allowNone and value is None:
            raise TypeError('%s must not be None' % self.name)
        if value is not None:
            value = type_safe_list(self, *value)
        objinfo = obj._attributes
        objinfo[self.name] = value
