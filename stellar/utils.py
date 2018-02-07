import requests
import sseclient

class HttpException(Exception):
    def __init__(self, msg, error=''):
        super(HttpException, self).__init__(msg)
        self.error = error

class Http(object):
    @staticmethod
    def get(url):
        try:
            json = requests.get(url).json()
            status = json['status'] if 'status' in json else 0
            if status > 400 and status <= 500:
                raise HttpException(json['title'], status)
        except requests.exceptions.RequestException as e:
            raise HttpException(str(e), -1)

        return json

    @staticmethod
    def post(url, data):
        try:
            json = requests.post(url, data).json()
            status = json['status'] if 'status' in json else 0
            if status > 400 and status <= 500:
                raise HttpException(json['title'], status)
        except requests.exceptions.RequestException as e:
            raise HttpException(str(e), -1)

        return json

    @staticmethod
    def stream(url):
        try:
            return sseclient.SSEClient(url)
        except requests.exceptions.RequestException as e:
            raise HttpException(str(e), -1)

