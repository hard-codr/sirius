import requests
import sseclient
import base64
import binascii

from decimal import Decimal
from stellarxdr import Xdr

class HttpException(Exception):
    def __init__(self, msg, error=''):
        super(HttpException, self).__init__(msg)
        self.error = error

class HTTP(object):
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


class XDR(object):
    #Returns xdr for stellar address where 
    #public address in format such as GBWF6NTCPGBROJIPF54XXYRLTUGBDLLORPFDK4FGQQ3IRI4T5PHCGVXV
    #or secret in format such as SDUHI5BSX67EA22KW7NWDREQNZBOYEYEBOHJ6N53WTG3WIEUCNMNC3HZ
    @staticmethod
    def address_to_xdr(address):
        decoded = base64.b32decode(address)
        return Xdr.types.PublicKey(Xdr.const.KEY_TYPE_ED25519, decoded[1:-2])

    #Returns amount xdr where amount is represent as long value and every decimal 
    #is multiplied by 10^7 to store it in max precision.
    @staticmethod
    def amount_to_xdr(amount):
        return int((Decimal(amount)*Decimal(10**7)).to_integral_exact())

    #Returns price xdr where price in (numerator, denominator) format
    @staticmethod
    def price_to_xdr(price):
        return Xdr.types.Price(price[0], price[1])

    #Returns asset code xdr where asset_code in string format e.g. 'USD', 'XLM' or 'MYCOOLASSET'
    @staticmethod
    def assetcode_to_xdr(asset_code):
        code_length = len(asset_code)
        pad_length = 4 - code_length if code_length <= 4 else 12 - code_length
        asset_code = bytearray(self.code, 'ascii') + b'\x00' * pad_length

        xdr = Xdr.nullclass()
        if code_length <= 4:
            xdr.type = Xdr.const.ASSET_TYPE_CREDIT_ALPHANUM4
            xdr.assetCode4 = asset_code
        else:
            xdr.type = Xdr.const.ASSET_TYPE_CREDIT_ALPHANUM12
            xdr.assetCode12 = asset_code

        return xdr

    #Returns signer xdr, where signer_type can be 'ed25519PublicKey', 'hashX', 'preAuthTX'
    @staticmethod
    def signer_key_to_xdr(signer_type, signer):
        if signer_type == 'ed25519PublicKey':
            return Xdr.types.SignerKey(Xdr.const.SIGNER_KEY_TYPE_ED25519, XDR.address_to_xdr(signer))
        if signer_type == 'hashX':
            return Xdr.types.SignerKey(Xdr.const.SIGNER_KEY_TYPE_HASH_X, hashX=signer)
        if signer_type == 'preAuthTX':
            return Xdr.types.SignerKey(Xdr.const.SIGNER_KEY_TYPE_PRE_AUTH_TX, preAuthTx=signer)
        raise Exception('Unknown signer_type = %s' % signer_type)

    #Returns asset xdr given asset in tuple format (asset_code, asset_issuer) or 'native'
    @staticmethod
    def asset_to_xdr(asset):
        def _to_xdr(asset_type, asset_code=None, asset_issuer=None):
            if asset_type == 'native':
                return Xdr.types.Asset(type=Xdr.const.ASSET_TYPE_NATIVE)
            else:
                code_length = len(asset_code)
                pad_length = 4 - code_length if code_length <= 4 else 12 - code_length

                xdr = Xdr.nullclass()
                xdr.assetCode = bytearray(asset_code, 'ascii') + b'\x00' * pad_length
                xdr.issuer = address_to_xdr(asset_issuer)

                if code_length <= 4:
                    return Xdr.types.Asset(type=Xdr.const.ASSET_TYPE_CREDIT_ALPHANUM4, 
                            alphaNum4=xdr)
                else:
                    return Xdr.types.Asset(type=Xdr.const.ASSET_TYPE_CREDIT_ALPHANUM12,
                            alphaNum12=xdr)

        if ((type(asset) == str or type(asset) == unicode) and asset == 'native') \
                or (len(asset) == 1 and asset[0] == 'native'):
                    return _to_xdr('native')
        else:
            if len(asset[0]) <= 4:
                return _to_xdr('credit_alphanum4', asset[0], asset[1])
            else:
                return _to_xdr('credit_alphanum12', asset[0], asset[1])

    #Returns memo xdr given memo in either string format or (type, value) format
    #where type in ('id', 'hash', 'return')
    @staticmethod
    def memo_to_xdr(memo):
        if type(memo) == str or type(memo) == unicode:
            #raise length error if len(memo) > 28
            return Xdr.types.Memo(type=Xdr.const.MEMO_TEXT, 
                    text=bytearray(memo, encoding='utf-8'))
        elif (type(memo) == tuple or type(memo) == list) and len(memo) == 2:
            if memo[0] == 'id':
                return Xdr.types.Memo(type=Xdr.const.MEMO_ID, id=int(memo[1]))
            elif memo[0] == 'hash':
                return Xdr.types.Memo(type=Xdr.const.MEMO_HASH, 
                        hash=binascii.unhexlify(memo[1]))
            elif memo[0] == 'return':
                return Xdr.types.Memo(type=Xdr.const.MEMO_RETURN, 
                        retHash=binascii.unhexlify(memo[1]))
            else:
                raise Exception('memo type [%s] not support' % memo[0])
        else:
            return Xdr.types.Memo(type=Xdr.const.MEMO_NONE)

    @staticmethod
    def time_bounds_to_xdr(time_bounds):
        return Xdr.types.TimeBounds(time_bounds[0], time_bounds[1])

