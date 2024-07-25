import os
import logging
import socket

from opensearchpy import helpers
from opensearchpy import OpenSearch, RequestsHttpConnection

logger = logging.getLogger()
logger.setLevel(logging.INFO)

DEFAULT_OPENSEARCH_HOST = 'vpc-emma-index-production-glc53yq4angokfgqxlmzalupqe.us-east-1.es.amazonaws.com'
DEFAULT_OPENSEARCH_INDEX = 'emma-federated-index-production'

EMMA_OPENSEARCH_REGION = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
EMMA_OPENSEARCH_SERVICE = 'es'

def get_host_and_port(urlstring, default_port = 443):
    url_parts = urlstring.partition(":")
    host = url_parts[0]
    port = int(url_parts[2]) if len(url_parts[2]) > 0 else default_port
    return host, port


class OpenSearchConnection :
   
    def __init__(self, url, index, tunnelhost = None, tunneluser = None, remoteurl = None, sshkey = None):
        self.url = url
        self.index = index
        self.host, self.port  = get_host_and_port(url, 443)
        if (not self.is_unused_port(self.port)) :
            self.port = self.find_unused_port(self.port, self.port+100)
        self.proxy =  (self.host == 'localhost') 

        self.tunnel_started = False 
        self.tunnel = None
        self.tunnelhost = tunnelhost
        self.tunneluser = tunneluser
        self.remotehost = None
        self.remoteport = None
        if (remoteurl) : 
            self.remotehost, self.remoteport = get_host_and_port(remoteurl, 443)
        self.sshkey = sshkey
        self.connection = None

    def make_tunnel(self):
        self.tunnel_started = False 
        if self.tunnelhost and self.tunneluser and self.remotehost and self.remoteport :
            # Setting up the SSH tunnel
            from sshtunnel import SSHTunnelForwarder
            self.tunnel = SSHTunnelForwarder(
                (self.tunnelhost, 22),
                ssh_username=self.tunneluser,
                ssh_pkey=self.sshkey,
                remote_bind_address=(self.remotehost, self.remoteport),
                local_bind_address=('localhost', self.port)
                )
            try:
                self.tunnel.start()
                logger.info("SSH tunnel established")
                self.tunnel_started = True
            except Exception as e:
                logger.info(f"Failed to establish SSH tunnel: {e}")
                raise e


    def connect(self):
        if not self.tunnel_started: 
            if self.tunnelhost and self.tunneluser and self.remotehost and self.remoteport and self.sshkey :
                self.make_tunnel()
        
        if not self.connection :
            if self.host and self.port:
                try :
                    logger.info("trying to connect to host " + self.host + " at port " + str(self.port) )
                    self.connection = OpenSearch(
                        hosts=[{'host': self.host, 'port': self.port}],
                        http_auth= None,
                        #http_auth=self.auth if not self.proxy else None,
                        use_ssl= True,
                        verify_certs= not self.proxy,
                        connection_class=RequestsHttpConnection,
                        # don't show warnings about ssl certs verification
                        ssl_show_warn=False)
                except Exception as e :
                    logger.exception(e)
                    raise e

    def bulk(self, bulk_upsert):
        try: 
            helpers.bulk(self.connection, bulk_upsert, max_retries=2)
        except Exception as e:
            logger.exception(e)
            raise e
            
    def close(self) :
        if (self.connection) :
            self.connection.transport.close()
            self.connection = None
            logger.info("Opensearch connection closed")

        if self.tunnel_started :
            self.tunnel.stop()
            self.tunnel_started = False
            logger.info("SSH tunnel closed")

    def is_unused_port(self, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('', port))
                return True
            except OSError:
                return False

    def find_unused_port(self, start_port, end_port):
        for port in range(start_port, end_port + 1):
            if self.is_unused_port(port) :
                return (port)
        raise RuntimeError("No unused ports available in the specified range.")
