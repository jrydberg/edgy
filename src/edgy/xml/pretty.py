# Copyright (C) 2008 Edgeware AB.
# Written by Johan Rydberg.

from edgy.xml.element import QName, _namespace_map, _escape_cdata
from cStringIO import StringIO
import string


def prefix_tag(prefix, tag):
    if prefix == "":
        return tag
    else:
        return "%s:%s" % (prefix, tag)


def fixtag(tag, namespaces):
    # given a decorated tag (of the form {uri}tag), return prefixed
    # tag and namespace declaration, if any
    if isinstance(tag, QName):
        tag = tag.text
    namespace_uri, tag = string.split(tag[1:], "}", 1)
    prefix = namespaces.get(namespace_uri)
    if prefix is None:
        prefix = _namespace_map.get(namespace_uri)
        if prefix is None:
            prefix = "ns%d" % len(namespaces)
        namespaces[namespace_uri] = prefix
        if prefix == "xml":
            xmlns = None
        else:
            xmlns = ("xmlns:%s" % prefix, namespace_uri)
    else:
        xmlns = None
    return prefix_tag(prefix, tag), xmlns


def pretty_print(file, node, indent=0):
    """Pretty print node to file."""
    def write(file, node, indent, namespaces):
        tag = node.tag
        items = node.items()
        xmlns_items = []
        if isinstance(tag, QName) or tag[:1] == '{':
            tag, xmlns = fixtag(tag, namespaces)
            if xmlns:
                xmlns_items.append(xmlns)
        file.write('%s' % (' ' * indent))
        file.write('<%s' % tag)
        if items or xmlns_items:
            items.sort()
            for k, v in items:
                if isinstance(k, QName) or k[:1] == '{':
                    k, xmlns = fixtag(k, namespaces)
                    if xmlns:
                        xmlns_items.append(xmlns)
                if isinstance(v, QName):
                    v, xmlns = fixtag(v, namespaces)
                    if xmlns:
                        xmlns_items.append(xmlns)
                file.write(" %s=\"%s\"" % (k, v))
            for k, v in xmlns_items:
                file.write(" %s=\"%s\"" % (k, v))
        if node.text or len(node):
            file.write(">")
            if node.text and node.text.strip():
                text = _escape_cdata(node.text.strip())
                file.write(text.encode('ascii', 'xmlcharrefreplace'))
                file.write('</%s>\n' % tag)
            else:
                file.write("\n")
                for n in node:
                    write(file, n, indent + 2, namespaces)
                file.write('%s</%s>\n' % (
                    indent * ' ', tag))
        else:
            file.write(" />\n")
        for k, v in xmlns_items:
            del namespaces[v]
    write(file, node, indent, {})


def tostring(node, encoding='UTF-8'):
    file = StringIO()
    pretty_print(file, node)
    return file.getvalue()
