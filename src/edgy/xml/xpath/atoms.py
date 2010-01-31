#
# pdis.xpath.atoms
#
# Copyright 2004 Helsinki Institute for Information Technology (HIIT)
# and the authors.  All rights reserved.
#
# Authors: Ken Rimey <rimey@hiit.fi>
#

# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
XPath syntax nodes for atoms
"""


from edgy.xml.xpath.xpath_exceptions import \
     XPathNotImplementedError, XPathEvaluationError

#
# Base classes
#
# These are generally abstract, except that the lexer instantiates
# QNames for its internal use.
#

class Name:
    def __init__(self, s):
        self.name = s

    def __str__(self):
        return self.name

class QName:
    def __init__(self, s1, s2=None):
        if s2 is None:
            self.prefix = None
            self.local_part = s1
        else:
            self.prefix = s1
            self.local_part = s2

    def __str__(self):
        if self.prefix is None:
            return self.local_part
        else:
            return "%s:%s" % (self.prefix, self.local_part)

#
# Atomic nodes never present in the final syntax tree
#
# These are used internal by the lexer and parser.  NameTest and
# NodeType are used as parameters in LocationStep nodes.  FunctionName
# is used as a parameter in FunctionCall nodes.
#

class AxisName(Name):
    pass

class NodeType(Name):
    pass

class NameTest(QName):
    # Here we allow local_part to take the otherwise illegal value "*".
    def expand(self, context):
        uri = context.namespace_mapping.get(self.prefix, None)
        if uri is None and self.prefix is not None:
            raise XPathEvaluationError, \
                  'Unbound namespace prefix "%s".' % self.prefix
        if self.local_part == '*':
            name = None
        else:
            name = self.local_part

        return (uri, name)

class FunctionName(QName):
    pass

#
# Atomic nodes
#

class Literal:
    """
    Node representing a string literal
    """
    def __init__(self, s):
        self.value = s

    def __str__(self):
        if '"' in self.value:
            return "'%s'" % self.value
        else:
            return '"%s"' % self.value

    def evaluate(self, context):
        return self.value

class Number:
    """
    Node representing a double-precision floating-point number
    """
    def __init__(self, value):
        self.value = float(value)

    def __str__(self):
        return str(self.value)

    def evaluate(self, context):
        return self.value

class VariableReference(QName):
    """
    Variable reference node
    """
    def __str__(self):
        return "$%s" % QName.__str__(self)

    def evaluate(self, context):
        raise XPathNotImplementedError, "Variable references not implemented."
