#
# pdis.xpath.test
#
# Copyright 2004 Helsinki Institute for Information Technology (HIIT)
# and the authors.  All rights reserved.
#
# Authors: Ken Rimey <rimey@hiit.fi>, Duncan McGreggor <oubiwann@adytum.us>
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

try:
    from pdis.lib.element import tostring as element_to_string
except ImportError:
    from elementtree.ElementTree import tostring as element_to_string

from pdis.xpath import evaluate

def tostring(x):
    if isinstance(x, (str, unicode)):
        return x
    elif isinstance(x, tuple):
        return "<<root node>>"
    else:
        return element_to_string(x)

def test_evaluate(path, document):
    """
    >>> test_evaluate("/", "<foo/>")
    ['<<root node>>']
    >>> test_evaluate("/*", "<foo/>")
    ['<foo />']
    >>> test_evaluate("/foo", "<foo/>")
    ['<foo />']
    >>> test_evaluate("/bar", "<foo/>")
    []
    >>> test_evaluate("/foo/two/text()", "<foo><one>1</one><two>2</two><three>3</three></foo>")
    ['2']
    >>> test_evaluate("/foo/two/text()", "<foo><two>1</two><two>2</two><two>3</two></foo>")
    ['1', '2', '3']
    >>> test_evaluate("/foo/two/text()", "<foo><one>1</one></foo>")
    []
    >>> test_evaluate("/foo", "<foo/>")
    ['<foo />']
    >>> test_evaluate("/bar", "<foo/>")
    []
    >>> test_evaluate("/foo/two/text()", "<foo><one>1</one><two>2</two><three>3</three></foo>")
    ['2']
    >>> test_evaluate("/foo/two/text()", "<foo><two>1</two><two>2</two><two>3</two></foo>")
    ['1', '2', '3']
    >>> test_evaluate("/foo/two/text()", "<foo><one>1</one></foo>")
    []
    >>> test_evaluate("/*/*/@color", "<foo><one/><two color='red'/><three color='blue'/></foo>")
    ['red', 'blue']
    >>> test_evaluate("/*/*/@color", "<foo><one/><two color='red'/><three flavor='sweet'/></foo>")
    ['red']
    >>> test_evaluate("/*/*[@color='red']", "<foo><one>1</one><two color='red'>2</two><three color='blue'>3</three></foo>")
    ['<two color="red">2</two>']
    >>> test_evaluate("/*/*[@color=/*/key]", "<foo><key>red</key><one>1</one><two color='red'>2</two><three color='blue'>3</three></foo>")
    ['<two color="red">2</two>']
    >>> test_evaluate("/*/*[@color[.='red']]", "<foo><one>1</one><two color='red'>2</two><three color='blue'>3</three></foo>")
    ['<two color="red">2</two>']
    >>> test_evaluate("/*/*[2]", "<foo><one>1</one><two>2</two><three>3</three></foo>")
    ['<two>2</two>']
    >>> test_evaluate("/*/*", "<foo>1<a>2</a>3<b>4</b>5<c>6</c>7</foo>")
    ['<a>2</a>3', '<b>4</b>5', '<c>6</c>7']
    >>> test_evaluate("/*/text()", "<foo>1<a>2</a>3<b>4</b>5<c>6</c>7</foo>")
    ['1', '3', '5', '7']
    >>> test_evaluate("/*/node()", "<foo>1<a>2</a>3<b>4</b>5<c>6</c>7</foo>")
    ['1', '<a>2</a>3', '3', '<b>4</b>5', '5', '<c>6</c>7', '7']
    >>> test_evaluate("/*/* | /*/text()", "<foo>1<a>2</a>3<b>4</b>5<c>6</c>7</foo>")
    ['<a>2</a>3', '<b>4</b>5', '<c>6</c>7', '1', '3', '5', '7']
    >>> test_evaluate("/*/* | /*/text()", "<foo>1<a>2</a>3<b>4</b>5<c>6</c>7</foo>")
    ['<a>2</a>3', '<b>4</b>5', '<c>6</c>7', '1', '3', '5', '7']
    >>> test_evaluate("(/*/one | /*/two)/@color", "<foo><one color='red'/><two color='green'/><three color='blue'/></foo>")
    ['red', 'green']
    >>> test_evaluate("/*/*[position() = last()]", "<foo><one>1</one><two>2</two><three>3</three></foo>")
    ['<three>3</three>']
    >>> test_evaluate("count(/*/*)", "<foo><one>1</one><two>2</two><three>3</three></foo>")
    3.0
    >>> test_evaluate("local-name(/*/*[text() = 1])", "<x:foo xmlns:x='blah'><x:one>1</x:one><x:two>2</x:two><x:three>3</x:three></x:foo>")
    one
    >>> test_evaluate("namespace-uri(/*/*[text() = 2])", "<x:foo xmlns:x='blah'><x:one>1</x:one><x:two>2</x:two><x:three>3</x:three></x:foo>")
    blah
    >>> test_evaluate("name(/*/*[text() = 3])", "<foo><one>1</one><two>2</two><three>3</three></foo>")
    three
    >>> test_evaluate("string(2 + 2 = 4)", "<foo/>")
    true
    >>> test_evaluate("concat(/*/one, '-', /*/*[last()])", "<foo><one>1</one><two>2</two><three>3</three></foo>")
    1-3
    >>> test_evaluate("/*/*[starts-with(., 'up')]", "<foo><one>Once</one><two>upon</two><three>a time.</three></foo>")
    ['<two>upon</two>']
    >>> test_evaluate("/*/*[contains(., 'e')]", "<foo><one>Once</one><two>upon</two><three>a time.</three></foo>")
    ['<one>Once</one>', '<three>a time.</three>']
    >>> test_evaluate('substring-before("1999/04/01", "/")', '<foo/>')
    1999
    >>> test_evaluate('substring-after("1999/04/01", "19")', '<foo/>')
    99/04/01
    >>> test_evaluate("substring('12345', 1.5, 2.6)", "<foo/>")
    234
    >>> test_evaluate("substring('12345', 0, 3)", "<foo/>")
    12
    >>> test_evaluate("translate('---aaa---', 'abc-', 'ABC')", "<foo/>")
    AAA
    >>> test_evaluate("boolean(3.2)", "<foo/>")
    True
    >>> test_evaluate("not(true())", "<foo/>")
    False
    >>> test_evaluate("not(false())", "<foo/>")
    True
    >>> test_evaluate("number('  03.14  ')", "<foo/>")
    3.14
    >>> test_evaluate("sum(/*/*)", "<foo><item>1</item><item>10</item><item>100</item></foo>")
    111.0
    >>> test_evaluate("concat(floor(3.5), ceil(3.5), round(3.5))", "<foo/>")
    344
    """
    result = evaluate(path, document)
    if isinstance(result, list):
        result = map(tostring, result)
    print result

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()
