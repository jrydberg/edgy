from zope.interface import Interface
from twisted.python.components import registerAdapter
from twisted.python import reflect

from edgy.model.model import Model, getNamedAttributes
from edgy.model import attributes
from txmongo import Database

import re


ID = '_id'
TYPENAME = '_typename'


def getCollectionName(typeClass):
    """
    Return the collection name where objects of C{typeClass} will be
    stored.
    """
    assert issubclass(typeClass, Model)
    cn = getattr(typeClass, '__collection__', None)
    if cn is None:
        c = typeClass
        while c.__bases__[0] != Model:
            c = c.__bases__[0]
        typeClass.__collection__ = cn = c.__name__.lower()
        #print "colleciton name", cn, "for", typeClass
    return cn


classRegistry = {}

def registerPresistentClass(typeClass, typeName=None):
    # get the collection name for the type class so that it is cached
    # in the __collection__ attribute.
    #print "register class"
    getCollectionName(typeClass)
    # calculate the typename of the class;
    if typeName is None:
        c = typeClass
        typeNames = []
        while c != Model:
            typeNames.append(c.__name__.lower())
            c = c.__bases__[0]
        typeName = ','.join(reversed(typeNames))
    typeClass.__typename__ = typeName
    typeClass.__typeregex__ = re.compile("^%s.*" % typeName)
    classRegistry[typeName] = typeClass


class IStore(Interface):

    def get(typeClass, objID):
        """
        Fetch object from database.
        """


def _fromObject(typeClass, pyval):
    d = {}
    for name, attribute in getNamedAttributes(typeClass, True):
        try:
            d[attribute.name] = _fromPyval(attribute, getattr(pyval, name))
        except AttributeError:
            pass
    if not d.has_key(ID):
        try:
            d[ID] = pyval._id
        except AttributeError:
            pass
    d[TYPENAME] = typeClass.__typename__
    return d


def _fromPyval(attribute, pyval):
    if isinstance(attribute, attributes.Timestamp):
        return pyval
    elif isinstance(attribute, attributes.Integer) \
            or isinstance(attribute, attributes.Double) \
            or isinstance(attribute, attributes.Boolean) \
            or isinstance(attribute, attributes.String):
        return pyval
    elif isinstance(attribute, attributes.Sequence):
        elementType = attribute.elementType
        if isclass(elementType):
            elementType = elementType()
        return [_fromPyval(elementType, v) for v in pyval]
    elif isinstance(attribute, attributes.Reference):
        return _fromObject(attribute.referenceType, pyval)

def _toPyval(attribute, spec):
    if isinstance(attribute, attributes.Timestamp):
        return spec
    elif isinstance(attribute, attributes.Integer) \
            or isinstance(attribute, attributes.Double) \
            or isinstance(attribute, attributes.Boolean) \
            or isinstance(attribute, attributes.String):
        return spec
    elif isinstance(attribute, attributes.Sequence):
        elementType = attribute.elementType
        if isclass(elementType):
            elementType = elementType()
        return [_toPyval(elementType, v) for v in spec]
    elif isinstance(attribute, attributes.Reference):
        return _toObject(attribute.referenceType, spec)


def _toObject(d):
    """
    """
    typeName = d.get(TYPENAME, None)
    if typeName is None:
        raise Exception("bad object")
    try:
        typeClass = classRegistry[typeName]
    except KeyError:
        raise
    o = typeClass(_do_not_finalize=True)
    #print o
    #print d
    #print d['lastName']
    for name, attribute in getNamedAttributes(typeClass, recurse=True):
        try:
            v = d[attribute.name]
            setattr(o, name, _toPyval(attribute, v))
        except AttributeError:
            raise
    o._id = d[ID]
    try:
        loadfn = o.__load__
    except AttributeError:
        pass
    else:
        loadfn()
    o._finalize()
    return o

operator_map = {
    '>' : '$gt',
    '>=': '@gte',
    '<' : '$lt',
    '<=': '$lte',
    '!=': '$ne',
}


class _Store(object):
    """

    @ivar _collections: cache of C{Collection} objects
    """

    def __init__(self, db):
        self.db = db
        self._collections = {}

    def _getCollection(self, typeClass):
        cn = getCollectionName(typeClass)
        if not cn in self._collections:
            self._collections[cn] = self.db[cn]
        return self._collections[cn]

    def _buildFindSpec(self, conditions):
        spec = {}
        for condition in conditions:
            if condition.operator == '==':
                v = condition.value
            else:
                v = {operator_map[condition.operator]:
                         condition.value}
            spec[condition.attribute.name] = v
        return spec

    def cbFind(self, docs):
        return [_toObject(doc) for doc in docs]

    def find(self, typeClass, *conditions, **kw):
        """
        """
        # UGLY workaround
        limit = kw.get('limit', 0)
        skip = kw.get('skip', 0)
        assert issubclass(typeClass, Model)
        spec = self._buildFindSpec(conditions)
        spec.update({TYPENAME: typeClass.__typeregex__})
        #print repr(spec)
        col = self._getCollection(typeClass)
        queryDeferred = col.find(spec, limit=limit, skip=skip)
        return queryDeferred.addCallback(self.cbFind)

    def cbSave(self, id, obj):
        """
        """
        #print "id", id, "obj", obj
        obj._id = id
        return obj

    def save(self, obj):
        """
        Save object into database.
        """
        #print "HEJ"
        assert isinstance(obj, Model)
        col = self._getCollection(obj.__class__)
        #print "col", col
        doc = _fromObject(obj.__class__, obj)
        #print "doc", doc
        return col.safe_save(doc).addCallback(self.cbSave, obj)

    def cbGet(self, docs):
        if len(docs) != 1:
            raise Exception("not found")
        return _toObject(docs[0])

    def get(self, typeClass, objID):
        """
        """
        assert issubclass(typeClass, Model)
        assert type(objID) == str 
        spec = {ID: objID}
        col = self._getCollection(typeClass)
        queryDeferred = col.find(spec, limit=-1)
        return queryDeferred.addCallback(self.cbGet)


registerAdapter(_Store, Database, IStore)


