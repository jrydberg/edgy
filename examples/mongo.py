from edgy.model import Integer, String, Reference, Sequence, Model
from edgy.model.mongodb import IStore, registerPresistentClass, _Store

from twisted.internet import defer, reactor
import txmongo

class Base(Model):
    firstName = String()

    def getName(self):
        return firstName

registerPresistentClass(Base)


class SuperBase(Base):
    lastName = String()

    def getName(self):
        return '%s, %s' % (self.lastName, self.firstName)

registerPresistentClass(SuperBase)


@defer.inlineCallbacks
def gotConnection(connection):
    """
    Invoked when we got the connection.
    """
    s = _Store(connection.foo)
    b = SuperBase(firstName="joe", lastName="smith")
    x = yield s.save(b)
    print "Object saved with id", x._id
    l = yield s.find(Base)
    for o in l:
        print "Hello", o.getName(), "(with id %r)" % o._id


def eb(result):
    result.printTraceback()

connDeferred = txmongo.MongoConnection()
connDeferred.addCallback(gotConnection)
connDeferred.addErrback(eb)

reactor.run()
