from zope.interface import implements, Interface, advice
from xtwisted.gwt import annotation, igwt
from twisted.python import components

from edgy.model.attributes import (String, Integer, Double, Sequence, Timestamp, 
                                   Boolean, Reference)
from edgy.model.model import getAttributes


def registerAttributeAdapter(attributeClass, typeClass):
    def adapter(original):
        return typeClass()
    components.registerAdapter(adapter, attributeClass, igwt.IType)

registerAttributeAdapter(Integer, annotation.Integer)
registerAttributeAdapter(String, annotation.String)
registerAttributeAdapter(Boolean, annotation.Boolean)
#registerAttributeAdapter(Sequence, annotation.ArrayList)
registerAttributeAdapter(Timestamp, annotation.Date)

def referenceAttributeAdapter(ref):
    typeClass = ref.referenceType
    return annotation.getTypeClassByTypeName(classRegistry[typeClass])

components.registerAdapter(referenceAttributeAdapter, Reference, igwt.IType)


def sequenceAttributeAdapter(seq):
    typeClass = seq.elementType
    try:
        return annotation.ArrayList(annotation.getTypeClassByTypeName(
                classRegistry[typeClass]))
    except KeyError:
        #return annotation.ArrayList(igwt.IType(typeClass))
        # FIXME - special case for sequence of String
        if typeClass == String:
            return annotation.ArrayList(annotation.String)
        raise
    
components.registerAdapter(sequenceAttributeAdapter, Sequence, igwt.IType)

classRegistry = {}

def registerRemoteClass(cls, remoteName=None, superClassName=None):
    """
    Register class C{cls} so that it can be identified as remote class
    C{remoteName}.
    """
    if remoteName is None:
        try:
            remoteName = cls.__remote_name__
        except AttributeError:
            pass
    if remoteName is None:
        raise Exception("remote name wasn't specified")

    _superType = None
    bases = cls.__bases__
    if len(bases) != 0:
        superClassNames = list()
        if superClassName is not None:
            superClassNames.append(superClassName)
        for base in bases:
            if base in classRegistry:
                superClassNames.append(classRegistry[base])
        if superClassNames:
            superClass = annotation.getTypeClassByTypeName(
                superClassNames[0]
                )
            _superType = superClass()
    else:
        _superType = annotation.Object()

    classRegistry[cls] = remoteName
    #print "superType", _superType
    
    class type_class(annotation.Type):
        @staticmethod
        def getTypeName():
            return remoteName
        superType = _superType

    annotation.registerTypeClass(type_class)

    
    attributes = {}
    for attribute in getAttributes(cls, recurse=False):
        attributes[attribute.name] = attribute

    print "class", remoteName, "has attributes", attributes.keys()

    class protocol_class(object):
        @staticmethod
        def names():
            return sorted(attributes.keys())
        @staticmethod
        def get(name):
            return annotation.RemoteAttribute(
                igwt.IType(attributes[name]))
    #annotation.typeProtocolRegistry.register(cls, protocol_class)
    annotation.registerTypeProtocol(type_class, protocol_class)

    class factory_class(object):
        def __init__(self, protocol_class):
            pass
        def buildInstance(self):
            return cls(_do_not_finalize=True)
    components.registerAdapter(factory_class, type_class,
                               igwt.IInstanceFactory)
    annotation.registerTypeAdapter(type_class, cls)

    
