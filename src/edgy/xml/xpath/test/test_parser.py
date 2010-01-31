#
# pdis.xpath.test_parser
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

def test_parser():
    """
    >>> from pdis.xpath.parser import parse_xpath as parse
    >>> print parse("/")
    /
    >>> print parse("foo")
    child::foo
    >>> print parse("/foo")
    /child::foo
    >>> print parse("//foo")
    /descendant-or-self::node()/child::foo
    >>> print parse("foo/bar")
    child::foo/child::bar
    >>> print parse("/foo/bar")
    /child::foo/child::bar

    >>> print parse("child::foo")
    child::foo
    >>> print parse("@foo")
    attribute::foo
    >>> print parse(".")
    self::node()
    >>> print parse("..")
    parent::node()

    >>> print parse("foo[one]")
    child::foo[child::one]
    >>> print parse("foo[one][two]")
    child::foo[child::one][child::two]

    >>> print parse("node()")
    child::node()
    >>> print parse("processing-instruction()")
    child::processing-instruction()
    >>> print parse("processing-instruction('whatever')")
    child::processing-instruction("whatever")

    >>> print parse("'foo'")
    "foo"
    >>> print parse("3.14")
    3.14
    >>> print parse("(3.14)")
    3.14
    >>> print parse("$work")
    $work

    >>> print parse("f()")
    f()
    >>> print parse("f(1)")
    f(1.0)
    >>> print parse("f(1, 2)")
    f(1.0, 2.0)

    >>> print parse("f()/blah")
    f()/child::blah
    >>> print parse("f()[maybe]")
    f()/self::node()[child::maybe]
    >>> print parse("f()[maybe]/blah")
    f()/self::node()[child::maybe]/child::blah

    >>> print parse("1 + 2 + 3 + 4 + 5")
    ((((1.0 + 2.0) + 3.0) + 4.0) + 5.0)
    >>> print parse("0 or 1 and 2 = 3 < 4 + 5 * 6 | 8")
    (0.0 or (1.0 and (2.0 = (3.0 < (4.0 + (5.0 * (6.0 | 8.0)))))))
    >>> print parse("1 + 2 * 3 | 4 * 5 + 6")
    ((1.0 + ((2.0 * (3.0 | 4.0)) * 5.0)) + 6.0)
    >>> print parse("1 | 2 * 3 + 4 * 5 | 6")
    (((1.0 | 2.0) * 3.0) + (4.0 * (5.0 | 6.0)))

    >>> print parse("1 * (2 + 3)")
    (1.0 * (2.0 + 3.0))
    >>> print parse("f() + f(1) + f(1, 2) + f(1, 2, 3)")
    (((f() + f(1.0)) + f(1.0, 2.0)) + f(1.0, 2.0, 3.0))
    >>> print parse("f(1 + 2, f(2, 3))")
    f((1.0 + 2.0), f(2.0, 3.0))
    >>> print parse("foo[1 + 2 = 3]")
    child::foo[((1.0 + 2.0) = 3.0)]
    >>> print parse("item[color = 'blue']")
    child::item[(child::color = "blue")]

    >>> print parse("1 * -2 * --3 * ---4")
    (((1.0 * (- 2.0)) * (- (- 3.0))) * (- (- (- 4.0))))
    >>> print parse("-1-2--3---4")
    ((((- 1.0) - 2.0) - (- 3.0)) - (- (- 4.0)))
    >>> print parse("-1 * -2|3 * -2|3|4")
    (((- 1.0) * (- (2.0 | 3.0))) * (- ((2.0 | 3.0) | 4.0)))
    """

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()

