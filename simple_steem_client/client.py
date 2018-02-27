
# Simple Steem client using urllib

import collections
import json
import logging
import time
import socket
import sys
import urllib.error
import urllib.request

class SteemException(Exception):
    pass

class SteemRPCException(SteemException):
    # Remote end returned error
    pass

class SteemHTTPError(SteemException):
    # HTTP error code
    pass

class SteemNetworkError(SteemException):
    pass

class SteemIllegalArgument(SteemException):
    # Buggy code in the caller is incorrectly using the provided API
    pass

class SteemRemoteBackend(object):
    """
    Implement the rpc_call() method which actually submits
    parameters to a remote node.
    """
    def __init__(self,
       nodes=[],
       urlopen=None,
       urlopen_args=[],
       urlopen_kwargs={},
       min_timeout=2.0,
       timeout_backoff=1.0,
       max_timeout=30.0,
       max_retries=-1,
       req_id=0,
       req_id_increment=1,
       sleep_function=None,
       appbase=False,
       json_encoder=None,
       json_decoder=None,
       ):
        """
        :param nodes:  List of Steem nodes to connect to
        :param urlopen:  Function used to load remote URL,
        urllib.request.urlopen is used if this parameter None or unspecified
        :param urlopen_args:  List of extra positional arguments to pass to the urlopen function
        :param urlopen_kwargs:  List of extra keyword arguments to pass to the urlopen function
        :param min_timeout:  Minimum amount of time to wait
        :param timeout_backoff:  Amount to increase timeout on HTTP failure code
        :param max_timeout:  Maximum amount of time to wait
        :param max_retries:  Maximum number of retries to attempt (-1 means try again forever)
        :param req_id:  The ID of the first request
        :param req_id_increment:  The amount by which subsequent request ID's should be incremented
        :param sleep_function:  time.sleep() or similar
        :param appbase:  If true, require keyword arguments.  If false, require positional arguments.
        :param json_encoder:  Used to encode JSON for requests.  If not supplied, uses json.JSONEncoder
        :param json_decoder:  Used to decode JSON from responses.  If not supplied, uses json.JSONDecoder
        """
        self.nodes = list(nodes)
        self.current_node = 0

        if urlopen is None:
            urlopen = urllib.request.urlopen
        self.urlopen = urlopen
        self.urlopen_args = list(urlopen_args)
        self.urlopen_kwargs = dict(urlopen_kwargs)

        self.min_timeout = min_timeout
        self.timeout_backoff = timeout_backoff
        self.max_timeout = max_timeout
        self.max_retries = max_retries

        self.req_id = req_id
        self.req_id_increment = req_id_increment
        if sleep_function is None:
            sleep_function = time.sleep
        self.sleep_function = sleep_function

        self.appbase = appbase

        if json_encoder is None:
            json_encoder = json.JSONEncoder(
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
                )
        self.json_encoder = json_encoder
        if json_decoder is None:
            json_decoder = json.JSONDecoder(
                object_pairs_hook=collections.OrderedDict,
                )
        self.json_decoder = json_decoder
        return

    def next_id(self):
        result = self.req_id
        self.req_id = result + self.req_id_increment
        return result

    def rpc_call(self,
        api="", method="",
        method_args=None,
        method_kwargs=None,
        ):

        if (method_args is not None) and (method_kwargs is not None):
            raise SteemIllegalArgument("Attempt to mix positional and keyword arguments")
        if self.appbase and (method_args is not None):
            raise SteemIllegalArgument("Post-appbase cannot specify args")
        if (not self.appbase) and (method_kwargs is not None):
            raise SteemIllegalArgument("Pre-appbase cannot specify kwargs")

        if len(self.nodes) == 0:
            raise SteemIllegalArgument("Must specify at least one node")

        if self.appbase:
            if method_kwargs is None:
                args = dict()
            else:
                args = method_kwargs
        else:
            if method_args is None:
                args = []
            else:
                args = method_args

        timeout = self.min_timeout
        retry_count = 0
        while True:
            req_id = self.next_id()
            d = collections.OrderedDict((
                ("jsonrpc", "2.0"),
                ("id", req_id),
                ("method", "call"),
                ("params", [api, method, args]),
                ))
            req_json = self.json_encoder.encode(d)
            req_bytes = req_json.encode("ascii")
            logging.info("req: %s", req_bytes)

            url = self.nodes[self.current_node]
            exc = None

            try:
                with self.urlopen(url, req_bytes, timeout,
                    *self.urlopen_args, **self.urlopen_kwargs) as f:
                    resp_bytes = f.read()
            except urllib.error.HTTPError as e:
                exc = sys.exc_info()
            except urllib.error.URLError as e:
                exc = sys.exc_info()
            except socket.timeout as e:
                exc = sys.exc_info()

            if exc is not None:
                logging.error("caught exception in request", exc_info=exc)
                retry_count += 1
                if (self.max_retries == -1) or (retry_count <= self.max_retries):
                    self.sleep_function(timeout)
                    timeout = min(timeout + self.timeout_backoff, self.max_timeout)
                    continue
                if isinstance(exc, urllib.error.HTTPError):
                    raise SteemHTTPError(exc)
                raise SteemNetworkError(exc)
            logging.info("resp: %s", resp_bytes)
            resp_json = resp_bytes.decode("utf-8")
            resp = self.json_decoder.decode(resp_json)
            if "error" in resp:
                raise SteemRPCException(resp)
            return resp["result"]

class SteemInterface(object):
    """
    Provide syntax to dynamically bind methods to a backend.
    """

    def __init__(self, backend=None):
        self.backend = backend
        return

    def __getattr__(self, item):
        if item.endswith("_api"):
            return SteemInterface.Api(api_name=item, backend=self.backend)
        raise AttributeError("Unknown attribute {!r}".format(item))

    class Api(object):
        def __init__(self, api_name="", backend=None):
            self.api_name = api_name
            self.backend = backend
            return

        def __getattr__(self, item):
            return SteemInterface.Method(
               api_name=self.api_name,
               method_name=item,
               backend=self.backend,
               )

    class Method(object):
        def __init__(self, api_name="", method_name="", backend=None):
            self.api_name = api_name
            self.method_name = method_name
            self.backend = backend
            return

        def __call__(self, *args, **kwargs):
            if len(args) == 0:
                args = None
            if len(kwargs) == 0:
                kwargs = None
            return self.backend.rpc_call(
                api=self.api_name,
                method=self.method_name,
                method_args=args,
                method_kwargs=kwargs,
                )
