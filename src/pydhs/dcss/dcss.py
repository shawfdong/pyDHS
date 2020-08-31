#
# this file comes from the Australian Light Source
#
import socket
import logging
import time


# small wrapper to make sure we are connected
def connected(func):
    def wrapper(self, *args, **kwargs):
        if not self.socket:
            self.connect()
        return func(self, *args, **kwargs)
    return wrapper


def debug(func):
    def wrapper(self, *args, **kwargs):
        self.debug = True
        return func(self, *args, **kwargs)
    return wrapper

# I feel that this class should be renamed from DCSS to DCSSConnector
class DCSSConnector(object):
    def __init__(self, server=None, port=None, SID=None):
        self.debug = False

        self.socket = None
        self.server = server
        self.port = port

        # socket recv buffer
        self.buffer = b''

        self.log = logging.getLogger('DCSS')

        # Instance variable for dcss login status
        self.dcss_client_loggedin = False

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        while True:
            try:
                self.log.info("Connecting to %s:%s" % (self.server, self.port))
                self.socket.connect((self.server, self.port))
            except socket.error:
                # Failure
                self.log.error('Failed to connect to %s:%s',
                               self.server, self.port)
                # Reduce frequency of connect attempts when having trouble
                # connecting
                time.sleep(5)
            else:
                # Success
                self.log.info("Connected to %s:%s" % (self.server, self.port))
                # we have 1 second to login after 'stoc_send_client_type'
                self.login()
                break

    @connected
    def readfully(self, bytes_to_read):
        bytes_to_read = int(bytes_to_read)
        if bytes_to_read == 0:
            return ''
        while len(self.buffer) < bytes_to_read:
            try:
                bytes_read = self.socket.recv(1024)
            except socket.error:
                self.log.info('EXDisconnected by dcss server at %s:%s',
                              self.server, self.port)
                return ''
            # If zero bytes read connection has been closed by dcss server
            if len(bytes_read) == 0:
                self.log.info('Disconnected by dcss server at %s:%s',
                              self.server, self.port)
                # Close the socket
                self.socket = None
                # Limit frequency of connection attempts
                time.sleep(5)
                return ''
            self.buffer += bytes_read

        data = self.buffer[:bytes_to_read].decode('utf-8')
        self.buffer = self.buffer[bytes_to_read:]
        return data

    def send_xos1(self, msg):
        msg = msg.encode('utf-8')
        if len(msg) >= 200:
            raise Exception("Message to long")
        self.log.debug('sending xos1: %r', msg)
        msg = b"%s\0" % msg
        try:
            self.socket.sendall(msg.rjust(200))
        except socket.error:
            # Just log the error
            self.log.info('Error sending msg to dcss server at %s:%s',
                          self.server, self.port)
        except AttributeError:
            self.log.info('Cannot send, not yet connected to dcss server at %s:%s',
                          self.server, self.port)

    def send_xos3(self, msg, data=b''):
        self.log.debug('sending xos3: %r', msg)
        msg = msg.encode('utf-8')
        header = b"%12d %12d " % (len(msg), len(data))
        packet = b"%s%s%s" % (header, msg, data)
        try:
            self.socket.sendall(packet)
        except socket.error:
            # Just log the error
            self.log.info('Error sending msg to dcss server at %s:%s',
                          self.server, self.port)
        except AttributeError:
            self.log.info('Cannot send, not yet connected to dcss server at %s:%s',
                          self.server, self.port)

    def read_header(self):
        header = self.readfully(26)
        if header == '':
            # Read fail
            return 0, 0
        else:
            # Read success
            return int(header[0:13]), int(header[14:26])

    def read_message(self):
        msg_len, data_len = self.read_header()
        msg = self.readfully(msg_len).rstrip('\0')
        data = self.readfully(data_len)
        # Log mesg if recv good
        if msg != '':
            self.log.debug('received: %r', msg)
        # process every message internally
        self._process_message(msg)
        # dont actually need data (only used for auth)
        return msg, data

    @connected
    def read_message_xos1(self):
        message = self.readfully(200).rstrip('\0')
        self.log.debug('received xos1: %r', message)
        # process every message internally
        self._process_message(message)
        return message

    def login(self):
        raise Exception('Must overide')

    def close(self):
        self.dcss_client_loggedin = False
        self.socket.close()

    def _process_message(self, msg):
        pass

    def process_messages(self):
        while True:
            yield self.read_message()[0]

    @debug
    def debug_loop(self):
        try:
            for _ in self.process_messages():
                pass
        except KeyboardInterrupt:
            self.log.info("Exiting on CTRL+C")
        finally:
            self.close()
            self.log.info("Done.")

    def process_until(self, msg_to_stop_on):
        for msg in self.process_messages():
            if msg.startswith(msg_to_stop_on):
                return msg
