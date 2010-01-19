from twisted.web.resource import Resource
from twisted.web import server, http, client, error
from twisted.internet import reactor, defer, reactor
from twisted.python import log, components
from edgy import xml
from zope.interface import Interface, implements
from urlparse import urlparse
import re
import time


class ControllerError(Exception):

    def __init__(self, responseCode):
        self.responseCode = responseCode


class UnsupportedRepresentationError(ControllerError):
    """
    The given representation was not supported by the controller.
    """

    def __init__(self):
        ControllerError.__init__(self, http.UNSUPPORTED_MEDIA_TYPE)


class NoSuchResourceError(ControllerError):

    def __init__(self):
        ControllerError.__init__(self, http.NOT_FOUND)


class Registry(object):

    def __init__(self):
        self.m = {}

    def get(self, k):
        return self.m.get(k, None)

    def register(self, k, v):
        self.m[k] = v


class ISerializer(Interface):

    def toRepr(dataObj):
        """
        Serialize data object into a representation.

        @rtype: a C{IRepresentation}
        """

    def fromRepr(dataRepr):
        """
        Deserialize representation into a data object.

        @arg dataRepr: a C{IRepresentation}
        """


serializerRegistry = Registry()

def registerSerializer(dataClass, serClass, *mimeTypes):
    """
    Register serializer class.
    """
    for mimeType in mimeTypes:
        serializerRegistry.register((dataClass, mimeType), serClass)

def getSerializer(dataClass, *mimeTypes):
    """
    Return the first serializer that could be found for the given data
    type and mime types.
    """
    for mimeType in mimeTypes:
        serClass = serializerRegistry.get((dataClass, mimeType))
        if serClass is not None:
            return serClass()
    raise UnsupportedRepresentationError()


def serializer(inputType):
    """
    Method decorator that deserializes a input representation into an
    object of the given input type.
    """
    def maker(fn):
        """
        Wrap-maker for functions that accept an input
        representation.
        """
        def wrapper(inputRepr):
            serializer = getSerializer(inputType, inputRepr.mineType)
            inputData = serializer.fromRepr(inputRepr)
            return fn(inputData)
        return wrapper
    return maker


class IRepresentation(Interface):
    pass


representationRegistry = Registry()

def registerRepresentation(reprClass):
    for mimeType in reprClass.mimeTypes:
        representationRegistry.register(mimeType, reprClass)


def getRepresentationClass(mimeType):
    cls = representationRegistry.get(mimeType)
    if cls is None:
        raise UnsupportedRepresentationError(mimeType)
    return cls


class _Representation(object):
    """

    @ivar headers: extra headers to send with the representation
    @type headers: C{dict}

    @ivar mimeType: the MIME type of the content that this
        representation represents. if C{None} it means that there
        is no content.
    """
    implements(IRepresentation)

    def __init__(self):
        self.headers = {}

    def setModificationTime(self, t):
        """
        Set that the representation has not been modified since the
        given time.
        """
        # FIXME: format time
        self.headeds['last-modified'] = t


class StringRepresentation(_Representation):
    """
    Representation where the content is a string.
    """
    mimeTypes = ('text/plain',)

    def __init__(self, content, mimeType=None):
        _Representation.__init__(self)
        if mimeType is None:
            mimeType = self.mimeTypes[0]
        self.mimeType = mimeType
        self.content = content

    def toString(self):
        """
        Return representation as a string that can be serialized.
        """
        return self.content

    def fromString(cls, string):
        """
        Return a C{StringRepresentation} with given content.
        """
        return cls(string)
    fromString = classmethod(fromString)

registerRepresentation(StringRepresentation)


class XMLRepresentation(_Representation):
    """
    Represention where the content is a XML document.
    """
    mimeTypes = ('text/xml',)

    def __init__(self, element):
        _Representation.__init__(self)
        self.mimeType = self.mimeTypes[0]
        self.element = element

    def toString(self):
        """
        Return representation as a string.
        """
        decl = '<?xml version="1.0" encoding="iso-8859-1"?>\n'
        return decl + xml.tostring(self.element) + '\n'

    def fromString(cls, string):
        """
        Return a C{XMLRepresentation} with given content.
        """
        return cls(xml.parse(string))
    fromString = classmethod(fromString)

registerRepresentation(XMLRepresentation)


class ReferenceRepresentation(_Representation):
    """
    Simple reference that has no content of its own, but references
    another resource with it's Location-header.
    """

    def __init__(self, location):
        _Representation.__init__(self)
        self.mimeType = None
        self.headers['location'] = location


class Controller:
    """
    @ivar attributes: controller attributes provided by router
    """

    def assertRepresentation(self, repr, *reprClasses):
        """
        Assert that representation C{repr} is of class C{reprClass}.
        """
        for reprClass in reprClasses:
            if isinstance(repr, reprClass):
                return reprClass
        raise UnsupportedRepresentationError()

    def init(self, router, request, url, **kw):
        """
        Initialize controller instance that is attached to specified
        request.
        """
        self.router = router
        self._request = request
        self.url = url
        self.attributes = kw

    def represent(self, data):
        """
        Return a representation for the given data.

        @rtype: object providing L{IRepresentation}
        """
        raise NotImplemented


def compile_regexp(url_def):
    """
    Compile url defintion to a regular expression.
    """
    elements = url_def.split('/')

    l = list()
    for element in elements:
        try:
            front, rest = element.split('{', 1)
            middle, end = rest.split('}', 1)

            expr = '(?P<%s>[0-9a-zA-Z\.\-_]+)' % middle.replace('-', '_')
            l.append(''.join([front, expr, end]))
        except ValueError:
            l.append(element)

    return '/'.join(l) + '$'


class Router(Resource, components.Componentized):
    isLeaf = True

    def __init__(self):
        self.controllers = list()
        components.Componentized.__init__(self)

    def addController(self, controllerPath, controllerClass):
        """
        Add router.
        """
        regexp = re.compile(compile_regexp(controllerPath))
        self.controllers.append((regexp, controllerClass))

    def getController(self, request):
        """
        Return an initialized controller based on the given request.
        """
        controllerUrl = request.URLPath()
        postpath = list(request.postpath)
        if not postpath[-1]:
            del postpath[-1]
        p = '/'.join(postpath)
        for regexp, controllerClass in self.controllers:
            m = regexp.match(p)
            if m is not None:
                controller = controllerClass()
                controller.init(self, request, controllerUrl.click(p), 
                                **m.groupdict())
                return controller
        print "no matching controller", p

    def ebControl(self, reason, request):
        reason.trap(ControllerError)
        request.setResponseCode(reason.value.responseCode)
        request.setHeader('content-length', '0')
        request.finish()

    def getPreferredRepresentations(self, request):
        """
        Return a list of preferred content types.
        """
        accept = request.getHeader('accept')
        content_types = list()
        for ct in accept.split(','):
            try:
                content_type, quality = ct.split(';')
            except ValueError:
                content_type = ct
            #if content_type[-2:-1] == '/*':
            #    content_type = content_type[:-2]
            #if content_type == '*':
            #    content_type = ''
            content_types.append(content_type.strip())
        return content_types

    def cbControl(self, (responseCode, output), request):
        """
        Callback from controller method.

        C{repr} is a provider of L{IRepresentation} that should be
        rendered to the client.
        """
        request.setResponseCode(responseCode)

        if output is not None:
            if not IRepresentation.providedBy(output):
                preferred = self.getPreferredRepresentations(request)
                serializer = getSerializer(type(output), *preferred)
                output = serializer.toRepr(output)

            for header, value in output.headers.items():
                request.setHeader(header, value)
            if output.mimeType is not None:
                request.setHeader('content-type', output.mimeType)
                data = output.toString()
                request.setHeader('content-length', len(data))
                request.write(data)
        request.finish()

    def render(self, request):
        """
        Render request.
        """
        controller = self.getController(request)
        if controller is None:
            request.setResponseCode(http.INTERNAL_SERVER_ERROR)
            return ''

        method = getattr(controller, request.method.lower(), None)
        if method is None:
            request.setResponseCode(http.NOT_ALLOWED)
            return ''
        
        input = []
        # If this request has some kind of content we need to turn
        # that into a representaiton before we do anything else.  We
        # choose representaiton based on Content-Type header.
        if request.method in ('POST', 'PUT'):
            contentType = request.getHeader('content-type')
            try:
                reprClass = getRepresentationClass(contentType)
            except UnsupportedRepresentationError, e:
                request.setResponseCode(e.responseCode)
                return ''
            input.append(reprClass.fromString(request.content.read()))

        doneDeferred = defer.maybeDeferred(method, *input)
        doneDeferred.addCallback(self.cbControl, request)
        doneDeferred.addErrback(self.ebControl, request)
        doneDeferred.addErrback(log.deferr)
        return server.NOT_DONE_YET


def _clientRequest(url, postdata, method, headers, timeout):
    """
    Integration function to the crappy client-interface of
    twisted.web.

    FIXME: we really need a better twisted.web client.
    """
    factory = client.HTTPClientFactory(url, postdata=postdata,
        method=method, headers=headers)
    factory.noisy = False

    schema, netloc, path, params, query, fragment = urlparse(url)
    try:
        hostname, port = netloc.split(':')
        port = int(port)
    except ValueError, e:
        hostname, port = netloc, 23232
    reactor.connectTCP(hostname, port, factory, timeout=timeout)
    def eb(reason):
        reason.trap(error.Error)
        if reason.value.status in ('204',):
            return ''
        return reason
    def cb(response):
        return (factory, response)
    return factory.deferred.addErrback(eb).addCallback(cb)


def clientRequest(url, dataRepr, method="GET", headers=None, timeout=5):
    """
    """
    def cb((response, content)):
        """
        Process incoming result.
        """
        contentTypes = response.response_headers.get('content-type', None)
        contentLengths = response.response_headers.get('content-length', None)
        if not contentTypes or not contentLengths:
            # FIXME: should we assume that it doesn't have any content
            # in this situation?
            return None
        contentType = contentTypes[0]
        contentLength = contentLengths[0]
        if contentLength and contentType:
            try:
                reprClass = getRepresentationClass(contentType)
            except UnsupportedRepresentationError, e:
                raise
            return reprClass.fromString(content)
        return None

    if headers is None:
        headers = {}
    if dataRepr is not None:
        headers['content-type'] = dataRepr.mimeType
        dataRepr = dataRepr.toString()

    headers['accept'] = 'text/xml' # FIXME: for now just do xml
    return _clientRequest(url, dataRepr, method, headers, timeout).addCallback(cb)
