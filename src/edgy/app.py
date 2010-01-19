"""
Application logic.
"""

from twisted.internet import reactor, defer
from twisted.python import usage, log, logfile, util
import sys
import os
import errno
import signal
import pdb


class Options(usage.Options):

    optFlags = (
        ('no-daemon', 'n', 'Do not daemonize'),
        ('debug', 'D', 'Run application in debugger'),
        )

    optParameters = (
        ('logfile',  'l', 'app.log', 'Specify log file'),
        ('pidfile',  'p', 'app.pid', 'Name of the pidfile'),
        ('uid',     None,      None, 'The uid to run as'),
        ('gid',     None,      None, 'The gid to run as'),
        )


class Application(object):
    """
    Base class for applications.
    """
    options = Options

    def startApplication(self, config):
        """
        Start application based on the based given configuration.

        @param config: L{usage.Options} instance 
        @return: a L{defer.Deferred} that will be called when the
            application has been initialized and started
        """
        raise NotImplemented

    def stopApplication(self):
        """
        Shut down application.

        @return: a L{defer.Deferred} that will be called when the
            application has been stopped
        """
        raise NotImplemented

    def reloadApplication(self):
        """
        Notification that someone has instructed the application to
        reload its configuration.
        """
        
def daemonize():
    # See http://www.erlenstar.demon.co.uk/unix/faq_toc.html#TOC16
    if os.fork():   # launch child and...
        os._exit(0) # kill off parent
    os.setsid()
    if os.fork():   # launch child and...
        os._exit(0) # kill off parent again.
    null = os.open('/dev/null', os.O_RDWR)
    for i in range(3):
        try:
            os.dup2(null, i)
        except OSError, e:
            if e.errno != errno.EBADF:
                raise
    os.close(null)


def fixPdb():
    def do_stop(self, arg):
        self.clear_all_breaks()
        self.set_continue()
        from twisted.internet import reactor
        reactor.callLater(0, reactor.stop)
        return 1

    def help_stop(self):
        print """stop - Continue execution, then cleanly shutdown the twisted reactor."""

    def set_quit(self):
        os._exit(0)

    pdb.Pdb.set_quit = set_quit
    pdb.Pdb.do_stop = do_stop
    pdb.Pdb.help_stop = help_stop


errflag = 0

def switchUID(uid, gid):
    """
    Switch uid and gid to what the user has specified on the command
    line.
    """
    if uid:
        uid = util.uidFromString(uid)
    if gid:
        gid = util.gidFromString(gid)
    util.switchUID(uid, gid)


def checkPID(pidfile):
    """
    Check that C{pidfile} does not point at an existing pid file that
    holds the PID of a running process.
    """
    if not pidfile:
        return
    if os.path.exists(pidfile):
        try:
            pid = int(open(pidfile).read())
        except ValueError:
            sys.exit('Pidfile %s contains non-numeric value' % pidfile)
        try:
            os.kill(pid, 0)
        except OSError, why:
            if why[0] == errno.ESRCH:
                # The pid doesnt exists.
                log.msg('Removing stale pidfile %s' % pidfile, isError=True)
                os.remove(pidfile)
            else:
                sys.exit("Can't check status of PID %s from pidfile %s: %s" %
                         (pid, pidfile, why[1]))
        else:
            sys.exit("""\
Another server is running, PID %s\n
This could either be a previously started instance of your application or a
different application entirely. To start a new one, either run it in some other
directory, or use the --pidfile and --logfile parameters to avoid clashes.
""" %  pid)


def removePID(pidfile):
    """
    Remove the specified PID file, if possible.  Errors are logged,
    not raised.

    @type pidfile: C{str}
    @param pidfile: The path to the PID tracking file.
    """
    if not pidfile:
        return
    try:
        os.unlink(pidfile)
    except OSError, e:
        if e.errno == errno.EACCES or e.errno == errno.EPERM:
            log.msg("Warning: No permission to delete pid file")
        else:
            log.err(e, "Failed to unlink PID file")
    except:
        log.err(None, "Failed to unlink PID file")


def runApplication(args, app):
    """
    Start specified application with the given arguments.
    """
    c = app.options()
    try:
        c.parseOptions(args)
    except usage.UsageError:
        raise
    checkPID(c['pidfile'])

    def cbStart(result):
        if not c['no-daemon']:
            daemonize()
        if c['pidfile']:
            f = open(c['pidfile'],'wb')
            f.write(str(os.getpid()))
            f.close()

    def ebStart(reason):
        print "EB", reason
        reason.printTraceback()
        global errflag
        errflag = 1
        reactor.stop()
        return reason

    def cbStop(result):
        removePID(c['pidfile'])
        return result

    def stopApp():
        stopDeferred = defer.maybeDeferred(app.stopApplication)
        stopDeferred.addBoth(cbStop)

    def reload():
        try:
            app.reloadApplication()
        except NotImplemented:
            pass

    def sigHUP(*args):
        reactor.callFromThread(reload)
    signal.signal(signal.SIGHUP, sigHUP)
        
    oldstdout, oldstderr = sys.stdout, sys.stderr
    switchUID(c['uid'], c['gid'])

    if c['logfile'] is not None:
        if c['logfile'] == '-':
            lf = sys.stdout
        else:
            lf = logfile.LogFile(os.path.basename(c['logfile']),
                                 os.path.dirname(c['logfile']) or '.')
        log.startLogging(lf)

    def start():
        startDeferred = defer.maybeDeferred(app.startApplication, c)
        startDeferred.addCallback(cbStart).addErrback(ebStart)
    reactor.callWhenRunning(start)

    reactor.addSystemEventTrigger('before', 'shutdown', stopApp)

    if c['debug']:
        sys.stdout = oldstdout
        sys.stderr = oldstderr
        signal.signal(signal.SIGUSR2, lambda *args: pdb.set_trace())
        signal.signal(signal.SIGINT, lambda *args: pdb.set_trace())
        fixPdb()
        pdb.runcall(reactor.run)
    else:
        reactor.run()
    
    if errflag:
        os.exit(1)
