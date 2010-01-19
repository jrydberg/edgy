from zope.interface import Interface, Attribute as ZopeAttribute, implements
from twisted.python import reflect
from edgy.xml import LocalNamespace as LOCAL
from edgy import iso8601
import re, time, datetime


class Context:

    def __init__(self):
        self.errors = []

    def error(self, fmt, *args):
        self.errors.append(fmt % args)


class IType(Interface):
    """Typed data.
    """

    def validateTypedValue(text, ctxt):
        """
        Validate the typed value of the text against the type
        defintion.

        @param text: the text string holding the value
        @type text: C{str}
        @param ctxt: context that the text is evaluated in
        @type ctxt: C{Context}
        @return: C{True} if the type validated correctly
        """

    def getTypedValue(text, ctxt):
        """
        Return typed value from the text that hold the canonical
        representation of the value.

        @param text: the text holding the typed value
        @type text: C{str}
        @param ctxt: context that the text is evaluated in
        @type ctxt: C{Context}
        @return: the value
        """

    def setTypedValue(value, ctxt):
        """
        Returns text content of the canonical representation of
        the types value.

        @param value: the typed value
        @param ctxt: context that the text is evaluated in
        @type ctxt: C{Context}
        @return: text holding typed value
        @rtype: C{str}
        """


class ISchemaNode(Interface):
    elements = ZopeAttribute("sequence of child elements")
    attributes = ZopeAttribute("sequence of attributes")


class SchemaNode(object):

    def __init__(self, name, **kw):
        if type(name) is type(''):
            name = LOCAL[name]
        self.name = name
        self.elements = list()
        self.parent = None

    def _attachChildren(self):
        for child in self.elements + self.attributes:
            child.attachParent(self)

    def attachParent(self, parent):
        """Attach this node to parent and module.
        """
        self.parent = parent

    def detachParent(self):
        """Detach from parent.
        """
        self.parent = None


class ElementNode(SchemaNode):
    minElements = 0
    maxElements = 1

    def __init__(self, name, **kw):
        SchemaNode.__init__(self, name)
        self.elements = list()
        reflect.accumulateClassList(reflect.getClass(self),
                                    'elements', self.elements)
        self.attributes = list()
        reflect.accumulateClassList(reflect.getClass(self),
                                    'attributes', self.attributes)
        self.__dict__.update(kw)
        #self._attachChildren()

    def extractElements(self, element, epos, checkAccess=False):
        """
        Extract elements from the given element.
        """
        if not element:         # empty list or None
            return [], epos
        start = epos
        while epos < len(element) and element[epos].tag == self.name:
            epos = epos + 1
        return element[start:epos], epos

    def checkNumElements(self, elements, ctxt):
        """
        Verify that the number of elements is correct according to
        the schema node.
        """
        if self.minElements is not None and len(elements) < self.minElements:
            ctxt.error('%s: too few elements', self.name)
        if self.maxElements is not None and len(elements) > self.maxElements:
            ctxt.error('%s: too many elements', self.name)

    def _iterate(self, element, ctxt, callable, pos=0):
        for schemaNode in self.elements:
            try:
                pos = callable(
                    element, schemaNode, pos, ctxt.decend(schemaNode.name)
                    )
            except errors.BaseError, error:
                ctxt.error(error)
        callable(element, None, pos, ctxt)
        return pos

    def validate(self, element, spos, ctxt):
        """
        Validate value against the element structure, in the provided
        context.
        """
        raise NotImplementedError("validate")

    def _validateAttributes(self, element, ctxt):
        for attributeNode in self.attributes:
            attributeNode.validate(childElement, ctxt)


class RootNode(ElementNode):
    """
    Root schema node that elements can be validated against.
    """

    def __init__(self, **kw):
        ElementNode.__init__(self, None, **kw)

    def _validate(self, element, ctxt):
        assert element is not None, "element is None"
        if element.tag != self.documentElement.name:
            ctxt.error('%s: missing element', self.documentElement.name)
            return
        return self.documentElement.validate([element], 0, ctxt)

    def validate(self, element):
        ctxt = Context()
        self._validate(element, ctxt)
        return ctxt.errors


class TypedNode:
    """
    Base functionality for nodes that are typed.
    """

    def __init__(self, type):
        self.type = IType(type)


class ListNode:
    """
    Base functionality for list nodes.
    """

    def extractKey(self, element, ctxt):
        """Extract key from the given element.
        """
        raise NotImplementedError("extractKey")

    def buildKeyElementMapping(self, elements, ctxt):
        """Build key-element mapping for the given elements.
        """
        m = {}
        for element in elements:
            m[self.extractKey(element, ctxt)] = element
        return m


class Container(ElementNode):
    """
    The container node is used to define an interior node in the
    schema tree.
    """
    
    def validate(self, element, epos, ctxt):
        """
        See ISchemaNode.validate.
        """
        elements, epos = self.extractElements(element, epos)
        self.checkNumElements(elements, ctxt)
        if not elements:
            return epos
        for childElement in elements:
            cpos = 0
            for attributeNode in self.attributes:
                attributeNode.validate(childElement, ctxt)
            for elementNode in self.elements:
                cpos = elementNode.validate(childElement, cpos, ctxt)
            if cpos < len(childElement):
                ctxt.error('%s: unknown element', element[cpos].tag)
        return epos


class Attribute(SchemaNode, TypedNode):
    """
    The C{Attribute} schema node is used to define attributes on
    elements.
    """
    mandatory = False

    def __init__(self, name, type, **kw):
        SchemaNode.__init__(self, name, **kw)
        TypedNode.__init__(self, type)

    def validate(self, element, ctxt):
        """
        Validate attributes against C{element}.
        """
        text = element.get(self.name, None)
        if text is None:
            if self.mandatory:
                ctxt.error('%s[%s]: attribute missing', element.tag,
                    self.name)
        else:
            if not self.type.validateTypedValue(text, ctxt):
                ctxt.error('%s[%s]: invalid value', element.tag,
                    self.name)
            

class Leaf(ElementNode, TypedNode):
    """
    The leaf statement is used to define a leaf node in the schema
    tree.
    """
    mandatory = False

    def __init__(self, name, type, **kw):
        ElementNode.__init__(self, name, **kw)
        TypedNode.__init__(self, type)

    def checkNumElements(self, elements, ctxt):
        """Verify that the number of elements is correct according to
        the schema node.
        """
        if len(elements) == 0:
            if self.mandatory:
                ctxt.error('%s: missing element', self.name)
        elif len(elements) > 1:
            ctxt.error('%s: bad element', self.name)

    def validate(self, element, epos, ctxt):
        """
        Validate leaf.
        """
        elements, epos = self.extractElements(element, epos)
        self.checkNumElements(elements, ctxt)
        for element in elements:
            self._validateAttributes(element, ctxt)
            text = element.text and element.text.strip() or ''
            if not self.type.validateTypedValue(text, ctxt):
                ctxt.error('%s: invalid value', self.name)
        return epos


class LeafList(ElementNode, ListNode, TypedNode):
    minElements = None
    maxElements = None

    def __init__(self, name, type, **kw):
        ElementNode.__init__(self, name, **kw)
        TypedNode.__init__(self, type)

    # ISchemaNode:
    def extractKey(self, element, ctxt):
        """
        See L{ListNode.extractKey}.
        """
        return element.text

    def validate(self, element, epos, ctxt):
        """
        See L{ElementNode.validate}.
        """
        elements, epos = self.extractElements(element, epos)
        self.checkNumElements(elements, ctxt)
        # validate according to type:
        values = list()
        for c, element in enumerate(elements):
            self._validateAttributes(element, ctxt)
            text = element.text and element.text.strip() or ''
            if self.type.validateTypedValue(text, ctxt):
                val = self.type.getTypedValue(text, ctxt)
                if val in values:
                    ctxt.error('%s: list element is not unique: %r',
                               self.name, val)
                values.append(val)
            else:
                ctxt.error('%s[%d]: invalid value', self.name, c)
        return epos





class _DerivativeType(object):
    implements(IType)

    def validateTypedValue(self, text, ctxt):
        return self.baseType.validateTypedValue(text, ctxt)

    def getTypedValue(self, text, ctxt):
        return self.baseType.getTypedValue(text, ctxt)

    def setTypedValue(self, value, ctxt):
        return self.baseType.setTypedValue(value, text)


class PatternType(_DerivativeType):

    def __init__(self, baseType, pattern):
        self.pattern = re.compile(pattern)
        self.baseType = baseType

    def validateTypedValue(self, text, ctxt):
        if self.baseType.validateTypedValue(text, ctxt):
            if self.pattern.match(text) is not None:
                return True


class BoolType(object):
    implements(IType)

    def validateTypedValue(self, text, ctxt):
        return text in ('true', 'false')

    def getTypedValue(self, text, ctxt):
        return {'true': True, 'false': False}[text]

    def setTypedValue(self, value, ctxt):
        return value and 'true' or 'false'


class StrType(object):
    implements(IType)

    def validateTypedValue(self, text, ctxt):
        return True

    def getTypedValue(self, text, ctxt):
        return text

    def setTypedValue(self, value, ctxt):
        return str(value)


class IntType(object):
    implements(IType)

    def validateTypedValue(self, text, ctxt):
        try:
            int(text)
        except ValueError:
            return False
        return True

    def getTypedValue(self, text, ctxt):
        return int(text)

    def setTypedValue(self, value, ctxt):
        return str(value)


class RangeType(_DerivativeType):
    implements(IType)

    def __init__(self, baseType, min, max):
        self.baseType = baseType
        self.min = min
        self.max = max

    def validateTypedValue(self, text, ctxt):
        if self.baseType.validateTypedValue(text, ctxt):
            value = self.baseType.getTypedValue(text, ctxt)
            return value >= self.min and value <= self.max



class ISO8601Type(object):
    implements(IType)

    def validateTypedValue(self, text, ctxt):
        try:
            iso8601.parse(text)
        except iso8601.ParseError:
            return False
        return True

    def getTypedValue(self, text, ctxt):
        t = iso8601.parse(text)
        return datetime.datetime.utcfromtimestamp(t)

    def setTypedValue(self, value, ctxt):
        # FIXME: should we present times in local-time here?
        tt = value.utctimetuple()
        t = time.mktime(tt)
        if value.microsecond:
            t = float(t) + (0.000001 * value.microsecond)
        return iso8601.tostring(t)
        

def main():
    from edgy.xml import Namespace 
    NS = Namespace(None)
    
    class AssetSchemaNode(Container):
        attributes = (
            Attribute('bool', BoolType()),
            Attribute('length', IntType()),
            Attribute('bitrate', IntType()),
            )

    class AssetSchema(RootNode):
        documentElement = AssetSchemaNode(NS['asset'])

    
    class Clip(Container):
        attributes = (
            Attribute('src',    StrType(), mandatory=True),
            Attribute('offset', IntType(), mandatory=True),
            Attribute('length', IntType(), mandatory=True),
            )

    class Playlist(Container):
        attributes = (
            Attribute('publish',   StrType()),
            Attribute('unpublish', StrType()),
            )
        elements = (
            Clip(NS['clip']),
            )

    class PlaylistSchema(RootNode):
        documentElement = Playlist(NS['playlist'])


    assetSchema = AssetSchema()
    ctxt = Context()
    element = NS['asset'](bool='true')
    assetSchema.validate(element, ctxt)
    print ctxt.errors
    
    element = NS['playlist']()
    PlaylistSchema().validate(element, ctxt)
    print ctxt.errors

    element = NS['playlist'](
        NS['clip'](src='/assets/xxx', offset='0', length='20')
        )
    PlaylistSchema().validate(element, ctxt)
    print ctxt.errors
    

if __name__ == '__main__':
    main()
