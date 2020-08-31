#
# this file comes from the Australian Light Source
#
import threading

from .pydhs.dcss import DCSSConnector


class OperationHandle(object):
    def __init__(self, dcss, name, handle):
        self.dcss = dcss
        self.name = name
        self.handle = handle

    def _send_formatted_msg(self, fmt, args):
        arg_str = ' '.join(str(arg) for arg in args)
        msg = fmt.format(name=self.name, handle=self.handle, args=arg_str)
        self.dcss.send_xos3(msg)

    def operation_completed(self, *args):
        fmt = 'htos_operation_completed {name} {handle} normal {args}'
        self._send_formatted_msg(fmt, args)

    def operation_error(self, *args):
        fmt = 'htos_operation_completed {name} {handle} error {args}'
        self._send_formatted_msg(fmt, args)

    def operation_update(self, *args):
        fmt = 'htos_operation_update {name} {handle} {args}'
        self._send_formatted_msg(fmt, args)

    def __repr__(self):
        cls_name = self.__class__.__name__
        return '<{} [{}]: {}>'.format(cls_name, self.handle, self.name)


class Server(DCSSConnector):
    """Distributed Hardware Server"""

    def __init__(self, name, server):
        super(Server, self).__init__(server=server, port=14242)
        self.name = name
        self.threads = []

    def login(self):
        msg = self.read_message_xos1()
        if msg != 'stoc_send_client_type':
            raise Exception('Unexpected message %s' % (msg, ))
        login_msg = "htos_client_is_hardware %s" % (self.name)
        self.send_xos1(login_msg)
        self.log.info("Logged in as hardware device '%s'" % self.name)
        self.dcss_client_loggedin = True

    def stoh_start_operation(self, name, handle, *args):
        func = getattr(self, name, None)
        if func is not None:
            handler = OperationHandle(self, name, handle)
            targs = [handler]
            targs.extend(args)
            t = threading.Thread(target=func, args=targs)
            self.threads.append(t)
            t.start()
        else:
            self.log.warning('Operation %s is unhandled' % name)

    def loop(self):
        while True:
            for msg in self.process_messages():
                try:
                    func_name, args = msg.split(None, 1)
                except ValueError:
                    # Bad recv
                    continue
                func = getattr(self, func_name, None)
                if func is not None:
                    func(*args.split())
                else:
                    self.log.info('DCSS function %s is not supported' % func_name)
