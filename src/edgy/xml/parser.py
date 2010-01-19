# Copyright (C) 2008 Edgeware AB.
# Written by Johan Rydberg.

"""Custom parser that create Elements of our kind.
"""

try:
    from xml.etree.ElementTree import (TreeBuilder, XMLTreeBuilder,
                                       parse as elementTreeParse)
except ImportError:
    from elementtree.ElementTree import (TreeBuilder, XMLTreeBuilder,
                                         parse as elementTreeParse)
from edgy.xml.element import Element
from cStringIO import StringIO


class CustomTreeBuilder(TreeBuilder):
    """Custom tree builder that not only uses our own factory but
    also creates parent-child relationship between the elements.
    """

    def __init__(self):
        TreeBuilder.__init__(self, Element)


def parse(source):
    """Parse elements.
    """
    parser = XMLTreeBuilder(target=CustomTreeBuilder())
    return elementTreeParse(StringIO(source), parser).getroot()


simpleParse = parse


