# Copyright (C) 2007 Edgeware Ab.
# Written by Rydberg Johan.

from edgy.xml.element import Element
from edgy.xml.xmlbuilder import QName, Namespace, LocalNamespace
from edgy.xml.parser import parse, simpleParse
from edgy.xml.pretty import tostring, pretty_print


def findtext(n, qname, default=None):
    for c in n.getchildren():
        #print repr(c), qname
        if c.tag == str(qname):
            return c.text
    return default


def find(n, qname, default=None):
    for c in n.getchildren():
        if c.tag == str(qname):
            return c
    return default


def findall(n, path):
    """Find all.
    """
    new = n.getchildren()[:]
    for comp in path:
        n = [c for c in new if c.tag == comp]
        #print repr(comp), repr(n)
        if n:
            new = []
            for c in n:
                new.extend(c.getchildren())
        if not n:
            break
    return n


def findAndRemove(n, *path):
    """Find instance issued by path and remove it.
    """
    for component in path:
        if n is None:
            break
        parent, n = n, find(n, component)
    if n is None:
        raise Exception("Bad path")
    parent.remove(n)
    return n


def geturi(prefix, namespaces):
    for p, uri in reversed(namespaces):
        if p == prefix:
            return uri
    return None # not found


def splitTag(tag):
    if tag[0] == '{':
        return tag[1:].split('}', 1)
    return None, tag

_split_tag = splitTag


def stripTag(tag):
    tag = str(tag)
    if tag[0] == '{':
        return tag[1:].split('}', 1)[1]
    return tag


