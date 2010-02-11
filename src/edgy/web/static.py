from twisted.web.http import datetimeToString
from twisted.web import static as base
from twisted.internet import reactor
from gzip import GzipFile
import time
import fnmatch


def parseAcceptEncoding(value):
    """
    Parse the value of an Accept-Encoding: request header.

    A qvalue of 0 indicates that the content coding is unacceptable; any
    non-zero value indicates the coding is acceptable, but the acceptable
    coding with the highest qvalue is preferred.

    @returns: A dict of content-coding: qvalue.
    @rtype: C{dict}
    """
    encodings = {}
    if value.strip():
        for pair in value.split(','):
            pair = pair.strip()
            if ';' in pair:
                params = pair.split(';')
                encoding = params[0]
                params = dict(param.split('=') for param in params[1:])
                priority = float(params.get('q', 1.0))
            else:
                encoding = pair
                priority = 1.0
            encodings[encoding] = priority

    if 'identity' not in encodings and '*' not in encodings:
        encodings['identity'] = 0.0001

    return encodings


def canCompress(req):
    """
    Check whether the client has negotiated a content encoding we support.
    """
    value = req.getHeader('accept-encoding')
    if value is not None:
        encodings = parseAcceptEncoding(value)
        return encodings.get('gzip', 0.0) > 0.0
    return False


class CompressingRequestWrapper(object):

    encoding = 'gzip'
    compressLevel = 6

    def __init__(self, original):
        self.underlying = original
        self._gzipFile = None
        self.method = original.method
        self.uri = original.uri
        self.setHeader('content-encoding', self.encoding)

        self.producer = None

    def isSecure(self):
        return self.underlying.isSecure()

    def getHeader(self, name):
        return self.underlying.getHeader(name)

    def redirect(self, url):
        return self.underlying.redirect(url)

    def setHeader(self, name, value):
        """
        Discard the Content-Length header.

        When compression encoding is in use, the Content-Length header must
        indicate the length of the compressed content; since we are doing the
        compression on the fly, we don't actually know what the length is after
        compression, so we discard this header. If this is an HTTP/1.1 request,
        chunked transfer encoding should be used, softening the impact of
        losing this header.
        """
        if name.lower() == 'content-length':
            return
        else:
            return self.underlying.setHeader(name, value)

    def registerProducer(self, producer, streaming):
        self.producer = producer
        reactor.callLater(0, self.producer.resumeProducing)
    def unregisterProducer(self, *args):
        pass

    def setLastModified(self, *args):
        return self.underlying.setLastModified(*args)

    def write(self, data):
        """
        Pass data through to the gzip layer.
        """
        if self._gzipFile is None:
            self._gzipFile = GzipFile(fileobj=self.underlying,
                mode='wb', compresslevel=self.compressLevel)
        self._gzipFile.write(data)
        if self.producer is not None:
            reactor.callLater(0, self.producer.resumeProducing)

    def finish(self):
        """
        Finish of gzip stream.
        """
        if self._gzipFile is None:
            self.write('')
        self._gzipFile.close()
        self.underlying.finish()


class File(base.File):
    """
    """

    cacheTime = (3 * 30 * 24 * 60 * 60)

    def __init__(self, path, defaultType="text/html", ignoredExts=[],
                 registry=None, allowExt=0, noCacheExts=None, 
                 noCompressExts=None):
        base.File.__init__(self, path, defaultType=defaultType,
            ignoredExts=ignoredExts, registry=registry, allowExt=allowExt)
        if not noCacheExts:
            noCacheExts = list()
        self.noCacheExts = noCacheExts
        if not noCompressExts:
            noCompressExts = list()
        self.noCompressExts = noCompressExts

    def _match(self, exts):
        for ext in exts:
            if self.path.endswith(ext):
                return True
        return False

    def render(self, request):
        """
        """
        if self._match(self.noCacheExts):
            request.setHeader("cache-control", "no-cache")
        else:
            request.setHeader("cache-control", "public")
            t = time.time() + self.cacheTime
            request.setHeader("expires", datetimeToString(t))
            request.setHeader("vary", "Accept-Encoding")

        if not self._match(self.noCompressExts):
            if canCompress(request):
                request = CompressingRequestWrapper(request)

        return base.File.render(self, request)

    def createSimilarFile(self, path):
        f = File(path, defaultType=self.defaultType, ignoredExts=self.ignoredExts, 
                 registry=self.registry, allowExt=0, noCacheExts=list(self.noCacheExts), 
                 noCompressExts=list(self.noCompressExts))
        # refactoring by steps, here - constructor should almost certainly take these
        f.processors = self.processors
        f.indexNames = self.indexNames[:]
        f.childNotFound = self.childNotFound
        return f
