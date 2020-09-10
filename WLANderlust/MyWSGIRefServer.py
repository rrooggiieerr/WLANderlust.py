import os, subprocess, socket, bottle

# Example code from https://stackoverflow.com/questions/11282218/bottle-web-framework-how-to-stop

class MyWSGIServer(bottle.ServerAdapter):
  server = None

  def run(self, handler):
    from wsgiref.simple_server import make_server, WSGIRequestHandler
    if self.quiet:
      class QuietHandler(WSGIRequestHandler):
        def log_request(*args, **kw): pass
      self.options['handler_class'] = QuietHandler
    self.server = make_server(self.host, self.port, handler, **self.options)
    self.server.serve_forever()

  def stop(self):
    self.server.shutdown()
    self.server.server_close()

class MySSLWSGIServer(MyWSGIServer):
  def __init__(self, host, port, **options):
    from pathlib import Path

    _ca_keyfile = '/etc/ssl/private/WLANderlust_CA.key'
    self.ca_certfile = '/etc/ssl/certs/WLANderlust_CA.crt'
    if not os.path.exists(_ca_keyfile):
      subprocess.run(['/usr/bin/openssl', 'genrsa', '-out', _ca_keyfile, '4096'])
      subprocess.run(['/usr/bin/openssl', 'req', '-new', '-x509', '-nodes', '-key', _ca_keyfile, '-out', self.ca_certfile, '-days', '3653', '-subj', '/O=WLANderlust/CN=WLANderlust Self Signed Root CA/'])

    #if not os.path.exists('/etc/ssl/index.txt'):
    #  Path('/etc/ssl/index.txt').touch()
    #  Path('/etc/ssl/index.txt.attr').touch()
    #  with open('/etc/ssl/serial', 'w') as f:
    #    f.write("01\n")

    _hostname = socket.getfqdn()
    self.ssl_keyfile = '/etc/ssl/private/%s.key' % _hostname
    self.ssl_certfile = '/etc/ssl/certs/%s.crt' % _hostname
    _req_file = '/etc/ssl/%s.req' % _hostname
    if not os.path.exists(self.ssl_keyfile):
      subprocess.run(['/usr/bin/openssl', 'genrsa', '-out', self.ssl_keyfile, '4096'])
      subprocess.run(['/usr/bin/openssl', 'req', '-new', '-nodes', '-key', self.ssl_keyfile, '-out', _req_file, '-subj', '/O=WLANderlust/CN=%s/' % _hostname])
      #subprocess.run(['/usr/bin/openssl', 'ca', '-extensions', 'server', '-policy', 'policy_anything', '-batch', '-cert', self.ca_certfile, '-in', _req_file, '-out', self.ssl_certfile, '-days', '3653'])
      subprocess.run(['/usr/bin/openssl', 'x509', '-req', '-in', _req_file, '-CA', self.ca_certfile, '-CAkey', _ca_keyfile, '-CAcreateserial', '-out', self.ssl_certfile, '-days', '3653'])

    super().__init__(host, port)

  def run(self, handler):
    from wsgiref.simple_server import make_server, WSGIRequestHandler
    import ssl
    if self.quiet:
      class QuietHandler(WSGIRequestHandler):
        def log_request(*args, **kw): pass
      self.options['handler_class'] = QuietHandler
    self.server = make_server(self.host, self.port, handler, **self.options)
    self.server.socket = ssl.wrap_socket(self.server.socket,
      keyfile = self.ssl_keyfile,
      certfile = self.ssl_certfile,  
      server_side = True)
    self.server.serve_forever()
