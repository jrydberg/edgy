# Copyright (C) 2008 Edgeware AB.
# Written by Johan Rydberg.

try:
    from xml.etree import ElementTree as ET
    from xml.etree.ElementTree import (iselement, QName, _namespace_map, 
                                       _escape_cdata)
except ImportError:
    from elementtree import ElementTree as ET
    from elementtree.ElementTree import (iselement, QName, _namespace_map, 
                                         _escape_cdata)

class Element(ET._ElementInterface):
    """Element interface.
    """

    def __init__(self, tag, attrib=None):
        if attrib is None:
            attrib = dict()
        ET._ElementInterface.__init__(self, tag, attrib)
        self.parent = None

    def adapt(self, element):
        """Adapter element.
        """
        element.setParent(self)

    def append(self, element):
        """Append element to this.
        """
        ET._ElementInterface.append(self, element)
        self.adapt(element)

    def insert(self, index, element):
        ET._ElementInterface.insert(self, index, element)
        self.adapt(element)

    def __setslice__(self, start, stop, elements):
        ET._ElementInterface.__setslice__(self, start, stop, elements)
        for element in elements:
            self.adapt(element)

    def remove(self, element):
        ET._ElementInterface.remove(self, element)
        element.setParent(None)

    def setParent(self, element):
        """Set parent of this element.
        """
        self.parent = element
