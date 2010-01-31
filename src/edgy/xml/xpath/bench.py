#
# pdis.xpath.bench
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

from time import time

try:
    from pdis.lib.element import XML
except ImportError:
    from elementtree.ElementTree import XML

from pdis.xpath import XPath

N = 10000

def bench(path, document):
    t0 = time()
    for i in range(N):
        element = XML(document)
    t1 = time()
    print t1 - t0, "(parse document)"

    t0 = time()
    for i in range(N):
        xpath = XPath(path)
    t1 = time()
    print t1 - t0, "(parse path)"

    t0 = time()
    for i in range(N):
        result = xpath.evaluate(element)
    t1 = time()
    print t1 - t0, "(evaluate)"

    print 'result =', result

document = "<item><blah>blah</blah><color>orange</color><blah>blah</blah></item>"
bench("/*/color = 'orange'", document)
bench("/*/color = 'green'", document)
