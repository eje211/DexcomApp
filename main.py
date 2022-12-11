from dataclasses import dataclass
from pydexcom import Dexcom
from typing import Optional, Awaitable, Any, Callable, Mapping
import logging
import json
from configparser import ConfigParser
from wsgiref.simple_server import make_server


logging.basicConfig(level=logging.CRITICAL)


dexcom_config = ConfigParser()
dexcom_config.read('dexcom.conf')

PORT = 8080


@dataclass
class Config:
    username = dexcom_config['Login']['USERNAME']
    password = dexcom_config['Login']['PASSWORD']


class DexcomClient:

    def __init__(self):
        self._dexcom: Optional[Dexcom] = None

    def _connect(self):
        """
        Connects to the Dexcom server and sets the "connected" instance
        attribute to True.
        """
        logging.info("Calling Dexcom...")
        self._dexcom = Dexcom(Config.username, Config.password)
        logging.info('Connected with Dexcom!')

    def get_reading(self):
        """
        Get the latest glucose reading from the associated transmitter.
        Connects first if the instance is not connected.
        :return: the latest glucose reading.
        """
        try:
            return self._update()
        except AttributeError:
            self._connect()
            return self._update()

    def _update(self):
        """
        Gets the latest glucose reading from the associated transmitter
        without connecting first.
        :return: The latest glucose reading.
        """
        blood_glucose = self._dexcom.get_current_glucose_reading()
        return {
            'glucose value': blood_glucose.value,
            'glucose trend': blood_glucose.trend_description
        }


dexcom = DexcomClient()


def app(environ: Mapping[str, Any], start_response: Callable[[str, list[tuple[str, str]]], None]) \
        -> list[bytes]:
    response_body = json.dumps(dexcom.get_reading())
    response_body = response_body.encode('utf8')
    path = environ['PATH_INFO']
    query = environ['QUERY_STRING']
    response_headers = [
        ('Content-Type', 'application/json'),
        ('Content-Length', str(len(response_body)))
    ]
    status = "200 OK"

    start_response(status, response_headers)

    return [response_body]
