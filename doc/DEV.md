# Scriptform Developer guide

## Build rules

Build rules for testing, generating documentation and generating packages are
stored in `build.sla`. These can be run directly from a POSIX compliant shell,
or you can use the [Simple Little Automator](https://github.com/fboender/sla)
for convenience.

## Inner workings

1. Instantiate a `ScriptForm` class. This takes care of loading the form
   config (json) file and provides methods to run the server.
2. If running as a daemon:
   a) Instantiate the `Daemon` class
   b) Hook up a callback to shutdown the ScriptForm server
   c) Start the daemon. This detaches from the console.
3. Start the ScriptForm server. This listens on a port for incoming HTTP
   connections.
4. If a request comes in, it is dispatched to the `ScriptFormWebApp` request
   handler. `ScriptFormWebApp` inherits from the `webserver.RequestHandler`
   class.  The `WebAppHandler` determines which method of `ScriptFormWebApp`
   the request should be dispatched to.
5. Depending on the request, a method is called on `ScriptFormWebApp`. These
   methods render HTML to as a response.
6. If a form is submitted, its fields are validated and the script callback is
   called. Depending on the output type, the output of the script is either
   captured and displayed as HTML to the user or directly streamed to the
   browser.
7. GOTO 4.
8. Upon receiving an OS signal (kill, etc) the daemon calls the shutdown
   callback.
9. The shutdown callback starts a new thread (otherwise the webserver blocks
   until the next request) to stop the server.
10. The program exits.
