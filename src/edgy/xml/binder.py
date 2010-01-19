from edgy.model.model import getAttributes
from edgy.model import Model, String, Integer, Timestamp, Sequence, Reference
from edgy.xml.schema import LeafList, Leaf, Container
from edgy.xml import Namespace, schema, tostring, stripTag, findall
from zope.interface import Interface, implements
from twisted.python import components
from datetime import datetime


class Binding:
    
    def __init__(self, documentElement, modelClass):
        self.documentElement = documentElement
        self.modelClass = modelClass
        self.aliases = {}


class MissingBinding(Exception):
    pass


class SchemaMissmatch(Exception):
    pass


class IConverter(Interface):
    pass


class Binder:

    def __init__(self):
        self.bindings = []
        self.converters = {}
        self.aliases = {}
        
    def getConverter(self, modelAttribute):
        return self.converters.get(modelAttribute, None)

    def alias(self, modelAttribute, tagName):
        self.aliases[modelAttribute] = tagName

    def consumeModelAttribute(self, mas, attribute_name):
        attribute_name = self.aliases.get(mas, attribute_name)
        model_attribute = mas.get(attribute_name, None)
        if model_attribute is None:
            raise SchemaMissmatch(attribute_name)
        #print "consumed", attribute_name
        del mas[attribute_name]
        return model_attribute

    def _gatherModelAttributes(self, obj):
        mas = {}
        for ma in getAttributes(obj.__class__, recurse=True):
            mas[ma.name] = ma
        return mas

    def _deserializeObject(self, schema, element, obj):
        # build a map of model attributues, index by the attribute
        # name: as attributes are consumed they are removed from the
        # map.
        mas = self._gatherModelAttributes(obj)

        for attributeNode in schema.attributes:
            model_attribute = self.consumeModelAttribute(mas, 
                stripTag(attributeNode.name))

            attribute_value = element.get(attributeNode.name, None)
            if attribute_value is None:
                continue

            attribute_value = attributeNode.type.getTypedValue(attribute_value, None)
            converter = self.getConverter(model_attribute)
            if converter:
                attribute_value = converter.convertTo(attribute_value)
            
            setattr(obj, model_attribute.name, attribute_value)

        index = 0
        for elementNode in schema.elements:
            model_attribute = self.consumeModelAttribute(mas, 
                stripTag(elementNode.name))
            converter = self.getConverter(model_attribute)

            elements = []
            while index < len(element) and element[index].tag == elementNode.name:
                elements.append(element[index])
                index += 1

            if isinstance(elementNode, Leaf):
                if not elements:
                    continue
                value = elementNode.type.getTypedValue(elements[0].text, None)
                if converter is not None:
                    value = converter.convertTo(value)
                setattr(obj, model_attribute.name, value)

            elif isinstance(elementNode, LeafList):
                values = []
                for subelement in elements:
                    value = elementNode.type.getTypedValue(subelement.text, None)
                    if converter is not None:
                        value = converter.convertTo(value)
                    values.append(value)
                setattr(obj, model_attribute.name, values)

            elif isinstance(elementNode, Container):
                if isinstance(model_attribute, Reference):
                    if not elements:
                        continue
                    cobj = model_attribute.referenceType(_do_not_finalize=True)
                    self._deserializeObject(elementNode, elements[0], cobj)
                    cobj._finalize()
                    setattr(obj, model_attribute.name, cobj)
                elif isinstance(model_attribute, Sequence):
                    values = []
                    for subelement in elements:
                        cobj = model_attribute.elementType(_do_not_finalize=True)
                        self._deserializeObject(elementNode, subelement, cobj)
                        cobj._finalize()
                        values.append(cobj)
                    setattr(obj, model_attribute.name, values)
                else:
                    assert False, "implement 2"
        return obj

    def _fromElement(self, binding, element):
        obj = binding.modelClass(_do_not_finalize=True)
        self._deserializeObject(binding.documentElement, element, obj)
        obj._finalize()
        return obj

    def fromElement(self, element):
        for binding in self.bindings:
            if binding.documentElement.name == element.tag:
                return self._fromElement(binding, element)
        raise MissingBinding(element.tag)
        

    def _serializeObject(self, schema, element, obj):
        # build a map of model attributues, index by the attribute
        # name: as attributes are consumed they are removed from the
        # map.
        mas = self._gatherModelAttributes(obj)

        # attributes:
        for attributeNode in schema.attributes:
            model_attribute = self.consumeModelAttribute(mas, 
                stripTag(attributeNode.name))

            # FIXME: should we call __get__ directly?
            attribute_value = getattr(obj, model_attribute.name, None)
            if attribute_value is None:
                continue
            converter = self.getConverter(model_attribute)
            if converter:
                attribute_value = converter.convertFrom(attribute_value)
            element.set(attributeNode.name,
                attributeNode.type.setTypedValue(attribute_value, None))

        # elements:
        for elementNode in schema.elements:
            model_attribute = self.consumeModelAttribute(mas, 
                stripTag(elementNode.name))

            # FIXME: should we call __get__ directly?
            attribute_value = getattr(obj, model_attribute.name, None)
            if attribute_value is None:
                continue
            converter = self.getConverter(model_attribute)
            if converter:
                attribute_value = converter.convertFrom(attribute_value)

            if isinstance(elementNode, Leaf):
                subelement = elementNode.name(
                    elementNode.type.setTypedValue(attribute_value, None))
                element.append(subelement)

            elif isinstance(elementNode, LeafList):
                for item in attribute_value:
                    subelement = elementNode.name(
                        elementNode.type.setTypedValue(item, None))
                    element.append(subelement)

            elif isinstance(elementNode, Container):
                if isinstance(model_attribute, Sequence):
                    for item in attribute_value:
                        subelement = elementNode.name()
                        self._serializeObject(elementNode, subelement, item)
                        element.append(subelement)
                elif isinstance(model_attribute, Reference):
                    if not type(attribute_value) in (list, tuple): #, iterator):
                        attribute_value = [attribute_value]
                    for item in attribute_value:
                        subelement = elementNode.name()
                        self._serializeObject(elementNode, subelement, item)
                        element.append(subelement)

        return element

    def _toElement(self, binding, modelObj):
        return self._serializeObject(binding.documentElement,
            binding.documentElement.name(), modelObj)
        

    def toElement(self, modelObj):
        """
        Turn model object C{modelObj} into a XML element.

        @return: a element
        @rtype: C{Element}
        """
        modelClass = modelObj.__class__
        for binding in self.bindings:
            if binding.modelClass is modelClass:
                return self._toElement(binding, modelObj)
        raise MissingBinding(modelClass)

    def bind(self, documentNode, modelClass):
        binding = Binding(documentNode, modelClass)
        self.bindings.append(binding)
        return binding

    def convert(self, modelAttribute, converter):
        self.converters[modelAttribute] = converter



global_binder = Binder()

# NS = Namespace("http://www.edgeware.tv/xmlns/cms/1.0", "cms")

# class _FooNode(schema.Container):
#     attributes = (
#         schema.Attribute('d', schema.IntType()),
#         )


# class _PlaylistNode(schema.Container):
#     """
#     Schema definition for the playlist-element in the playlist
#     controller.
#     """
#     attributes = (
#         schema.Attribute('a', schema.IntType(),
#             mandatory=True),
#         schema.Attribute('b', schema.StrType(),
#             mandatory=True),
#         )
#     elements = (
#         schema.Leaf(NS['t'], schema.ISO8601Type()),
#         schema.LeafList(NS['s'], schema.ISO8601Type()),
#         _FooNode(NS['z']),
#         _FooNode(NS['h']),
#         )


# class PlaylistSchema(schema.RootNode):
#     documentElement = _PlaylistNode(NS['my-model'])

# playlistSchema = PlaylistSchema()



# class Foo(Model):
#     d = Integer()

# class MyModel(Model):
#     a = Integer()
#     b = String()
#     t = Timestamp()
#     s = Sequence(Timestamp)
#     z = Reference(Foo, optional=True, allowNone=True)
#     h = Sequence(Foo, optional=True)

# global_binder.bind(playlistSchema.documentElement, MyModel)


# m = MyModel(a=0, b='hello', t=datetime.utcnow(), s=[], z=Foo(d=10), h=[Foo(d=20), Foo(d=30)])
# e = global_binder.toElement(m)
# print tostring(e)

# m2 = global_binder.fromElement(e)
# print m2
# print m
