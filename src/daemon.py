import logging
import os
import sys
import signal
import time
import errno
import atexit


class DaemonError(Exception):
    pass


class Daemon:  # pragma: no cover
    """
    Daemonize the current process (detach it from the console).
    """
    def __init__(self, pid_file, log_file=None, log_level=logging.INFO,
                 foreground=False):
        if pid_file is None:
            self.pid_file = '{0}.pid'.format(os.path.basename(sys.argv[0]))
        else:
            self.pid_file = pid_file
        if log_file is None:
            self.log_file = '{0}.log'.format(os.path.basename(sys.argv[0]))
        else:
            self.log_file = log_file
        self.foreground = foreground

        logging.basicConfig(level=log_level,
                            format='%(asctime)s:%(name)s:%(levelname)s:%(message)s',
                            filename=self.log_file,
                            filemode='a')
        self.log = logging.getLogger('DAEMON')
        self.shutdown_cb = None

    def register_shutdown_cb(self, cb):
        self.shutdown_cb = cb

    def start(self):
        self.log.info("Starting")
        if self.is_running():
            self.log.error('Already running')
            raise DaemonError("Already running")
        if not self.foreground:
            self._fork()

    def stop(self):
        if not self.is_running():
            raise DaemonError("Not running")

        pid = self.get_pid()

        # Kill the daemon and wait until the process is gone
        os.kill(pid, signal.SIGTERM)
        for timeout in range(25):  # 5 seconds
            time.sleep(0.2)
            if not self._pid_running(pid):
                break
        else:
            self.log.error("Couldn't stop the daemon.")

    def is_running(self):
        """
        Check if the daemon is already running by looking at the PID file
        """
        if self.get_pid() is None:
            return False
        else:
            return True

    def get_pid(self):
        """
        Returns the PID of this daemon. If the daemon is not running (the PID
        file does not exist or the PID in the PID file does not exist), returns
        None.
        """
        if not os.path.exists(self.pid_file):
            return None

        try:
            pid = int(file(self.pid_file, 'r').read().strip())
        except ValueError:
            return None

        if os.path.isdir('/proc/{0}/'.format(pid)):
            return pid
        else:
            os.unlink(self.pid_file)
        return None

    def _pid_running(self, pid):
        """
        Returns True if the PID is running, False otherwise
        """
        try:
            os.kill(pid, 0)
        except OSError as err:
            if err.errno == errno.ESRCH:
                return False
        return True

    def _fork(self):
        # Fork a child and end the parent (detach from parent)
        pid = os.fork()
        if pid > 0:
            sys.exit(0)  # End parent

        # Change some defaults so the daemon doesn't tie up dirs, etc.
        os.setsid()
        os.umask(0)

        # Fork a child and end parent (so init now owns process)
        pid = os.fork()
        if pid > 0:
            self.log.info("PID = {0}".format(pid))
            f = file(self.pid_file, 'w')
            f.write(str(pid))
            f.close()
            sys.exit(0)  # End parent

        atexit.register(self._cleanup)
        signal.signal(signal.SIGTERM, self._cleanup)

        # Close STDIN, STDOUT and STDERR so we don't tie up the controlling
        # terminal
        for fd in (0, 1, 2):
            try:
                os.close(fd)
            except OSError:
                pass

        # Reopen the closed file descriptors so other os.open() calls don't
        # accidentally get tied to the stdin etc.
        os.open("/dev/null", os.O_RDWR)  # standard input (0)
        os.dup2(0, 1)                    # standard output (1)
        os.dup2(0, 2)                    # standard error (2)

        return pid

    def _cleanup(self, signal=None, frame=None):
        self.log.info("Received signal {0}".format(signal))
        if os.path.exists(self.pid_file):
            os.unlink(self.pid_file)
        self.shutdown_cb()
