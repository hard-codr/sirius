# -*- coding: utf-8 -*-

import ed25519
import crc16
import sseclient
import json
import base64
import datetime
import binascii
import hashlib
import struct

from .xdr import Xdr
from .utils import HTTP, XDR, FED
from .keys import account_from_secret

HORIZON_PUBLIC_ENDPOINT = 'https://horizon.stellar.org'
HORIZON_TESTNET_ENDPOINT = 'https://horizon-testnet.stellar.org'

NETWORK_PASSWORD_PUBLIC = 'Public Global Stellar Network ; September 2015'
NETWORK_PASSWORD_TESTNET = 'Test SDF Network ; September 2015'

BASE_FEE = 100

horizon = HORIZON_TESTNET_ENDPOINT
network_password = NETWORK_PASSWORD_TESTNET
network_id = hashlib.sha256(network_password).digest()

def setup_test_network():
    """Sets the current network to stellar.org test network"""
    global horizon, network_id, network_password
    horizon = HORIZON_TESTNET_ENDPOINT
    network_password = NETWORK_PASSWORD_TESTNET
    network_id = hashlib.sha256(network_password).digest()

def setup_public_network():
    """Sets the current network to stellar.org public network"""
    global horizon, network_id, network_password
    horizon = HORIZON_PUBLIC_ENDPOINT
    network_password = NETWORK_PASSWORD_PUBLIC
    network_id = hashlib.sha256(network_password).digest()

def setup_custom_network(horizon_url, password):
    """Sets network to custom horizon endpoint"""
    global horizon, network_id, network_password
    horizon = horizon_url
    network_password = password
    network_id = hashlib.sha256(network_password).digest()

def get_current_network():
    """Returns tuple containing horizon endpoint url and current network_id"""
    global horizon, network_id, network_password
    return (horizon, network_id)

#Shortens address for display purpose
def _shorten_address(address):
    return '%s__%s' % (address[:4], address[-4:])

def _get_seed_from_secret(secret):
    decoded = base64.b32decode(secret)
    return decoded[1:-2]

#Signs given trx_hash with provided secret key
def _sign_trx_hash(signer, trx_hash):
    signing_key = ed25519.SigningKey(_get_seed_from_secret(signer))
    public_key = Xdr.types.PublicKey(Xdr.const.KEY_TYPE_ED25519, 
            signing_key.get_verifying_key().to_bytes())
    signature = signing_key.sign(trx_hash)
    hint = bytes(public_key.ed25519[-4:])
    return Xdr.types.DecoratedSignature(hint, signature)    

#if input is federation address resolve it to account-id
def _address_to_account(address):
    if '*' in address:
        return FED.resolve_to_account(address)
    return address

class Asset(object):
    """ Asset represents either stellar native asset or asset code with given issuer """
    def __init__(self, data, prefix=''):
        """Constructs Asset given data dict having following keys: asset_type, 
        asset_code, asset_issuer.  if asset_type is 'native' then rest of the 
        fields are not needed. If prefix is passed then all above keys are 
        prefixed with it and then searched in the dict, e.g. if prefix = 'sender'
        then 'sender_asset_type', etc will be searched instead of default asset_type.
        """
        type_key = prefix + 'asset_type' 
        self.asset_type = data[type_key]
        '''asset type (either native, credit_alphanum4 or credit_alphanum12)'''
        self.asset_code = None
        '''asset code for asset'''
        self.asset_issuer = None
        '''asset issuer of the non-native asset'''
        self.limit = None
        '''limit on holding the asset if any'''
        if self.asset_type != 'native':
            self.asset_code = data[prefix + 'asset_code']
            self.asset_issuer = data[prefix + 'asset_issuer']
            limit_key = (prefix + 'limit')
            if limit_key in data:
                self.limit = data[limit_key]
        else:
            self.asset_code = 'XLM'

    def __repr__(self):
        return 'Asset(native)' if self.asset_type == 'native' else 'Asset(%s,%s,%s)'\
                % (self.asset_type, self.asset_code, _shorten_address(self.asset_issuer))

    @staticmethod
    def format_url_parameters(asset, prefix=''):
        """Formats asset for url parameter. e.g. asset_type=credit_alphanum4&asset_code=USD&asset_issuer=GFED..CBAH
        asset is tuple in form (asset_code,asset_issuer) or 'native'
        if prefix is given then url parameter will be prefixed with it.
        """
        if ((type(asset) == str or type(asset) == unicode) and asset == 'native') \
                or (len(asset) == 1 and asset[0] == 'native'):
            return '%sasset_type=native' % prefix
        else:
            if len(asset) == 1:
                raise ValueError('Needed asset in (asset_code, asset_issuer) format or "native"')
            if len(asset[0]) <= 4:
                return '%sasset_type=credit_alphanum4&%sasset_code=%s&%sasset_issuer=%s'\
                        % (prefix, prefix, asset[0], prefix, asset[1])
            else:
                return '%sasset_type=credit_alphanum12&%sasset_code=%s&%sasset_issuer=%s'\
                        % (prefix, prefix, asset[0], prefix, asset[1])

#constant representing stellar native asset (lumens, XLM)
native_asset = Asset({'asset_type' : 'native'})

class Fetchable(object):
    """Base class representing resource that can be retrieved from horizon endpoint. 
    Resource can be fetched or streamed. Fetched object returns single object for point queries
    or Page object for paginated queries. Stream object returns generator which 
    can be iterated.
    """
    class Page(object):
        """Page containing records, link to next page and previous page. """
        def __init__(self, mapper, data):
            self.mapper = mapper
            self.records = [self.mapper(r) for r in data['_embedded']['records']]
            self.nextlink = data['_links']['next']['href']
            self.prevlink = data['_links']['prev']['href']

        def entries(self):
            """returns records in current page"""
            return self.records

        def next(self):
            """fetches next page from the network and returns page object"""
            r = HTTP.get(self.nextlink)
            return Fetchable.Page(self.mapper, r)

        def prev(self):
            """fetches prev page from the network and returns page object"""
            r = HTTP.get(self.prevlink)
            return Fetchable.Page(self.mapper, r)

    def fetch(self, cursor=None, limit=10, order='asc'):
        """Returns single or page object for given query. If paged object
        then optionally accepts cursor (default none), limit (default 10)
        and order (default asc). order can be 'asc' or 'desc'.
        """
        if self.paginated:
            urlsep = '&' if self.url.find('?') >= 0 else '?' 
            if cursor:
                self.url = '%s%scursor=%s&limit=%s&order=%s' %\
                        (self.url, urlsep, cursor, limit, order)
            else:
                self.url = '%s%slimit=%s&order=%s' % (self.url,\
                        urlsep, limit, order)

        r = HTTP.get(horizon + self.url)
        if not self.paginated:
            return self._map2obj(r)
        return Fetchable.Page(lambda x : self._map2obj(x), r)

    def first(self):
        """Helper method for paginated query. returns first record for given paged
        resource or None if thier are not records for given query. 
        e.g. to fetch first transaction:

            >>> stellar.transactions().first()
        """
        r = self.fetch(limit=1, order='asc').records
        if len(r) > 0:
            return r[0]
        else:
            return None

    def last(self):
        """Helper method for paginated query. returns last record for given paged
        resource or None if thier are not records for given query.
        e.g. to fetch last transaction:

            >>> stellar.transactions().last()
        """
        r = self.fetch(limit=1, order='desc').records
        if len(r) > 0:
            return r[0]
        else:
            return None

    def stream(self, cursor=None, limit=10, order='asc'):
        """Returns iterable stream for the given query.
        You can start stream from given cursor and order specified in the input.
        Returned stream can be iterable using for-loop.
        """
        if self.streamed:
            urlsep = '&' if self.url.find('?') >= 0 else '?' 
            if cursor:
                self.url = '%s%scursor=%s&limit=%s&order=%s' %\
                        (self.url, urlsep, cursor, limit, order)
            else:
                self.url = '%s%slimit=%s&order=%s' % (self.url,\
                        urlsep, limit, order)

            eventsource = HTTP.stream(horizon + self.url)
            for event in eventsource:
                if event.data == '"hello"':
                    continue
                yield self._map2obj(json.loads(event.data))
        else:
            raise Exception('stream not supported')

    def _map2obj(self, data):
        """Function that subclass need to implemet to convert parsed json object to
        python object, according to resource that is requested
        """
        pass

class Accounts(Fetchable):
    class Thresholds(object):
        def __init__(self, data):
            self.low_threshold = int(data['low_threshold'])
            self.med_threshold = int(data['med_threshold'])
            self.high_threshold = int(data['high_threshold'])

        def __repr__(self):
            return 'Thresholds(l=%s, m=%s, h=%s)' % (self.low_threshold, self.med_threshold, self.high_threshold)

    class Flags(object):
        def __init__(self, data):
            self.auth_required = data['auth_required']
            self.auth_revocable = data['auth_revocable']

        def __repr__(self):
            return 'Flags(required=%s, revocable=%s)' % (self.auth_required, self.auth_revocable)

    class Balance(object):
        def __init__(self, data):
            self.balance = data['balance']
            self.asset = Asset(data)

        def __repr__(self):
            return 'Balance(%s %s)' % (self.balance, self.asset.asset_code)

    class Signer(object):
        def __init__(self, data):
            self.public_key = data['public_key']
            self.weight = int(data['weight'])
            self.key = data['key']
            self.type = data['type']

        def __repr__(self):
            return 'Signer(%s, %s)' % (_shorten_address(self.public_key),  self.weight)

    class Data(object):
        def __init__(self, data):
            self.key = data['key']
            self.value = base64.b64decode(data['value'])

        def __repr__(self):
            return 'Data(%s, %s)' % (self.key, self.value)

    class Account(object):
        """Account:https://www.stellar.org/developers/horizon/reference/resources/account.html"""
        def __init__(self, data):
            """Construct Account object given data dict having all the account related field."""
            self.account_id = data['id']
            self.paging_token = data['paging_token']
            self.sequence = data['sequence']
            self.subentry_count = int(data['subentry_count'])
            self.thresholds = Accounts.Thresholds(data['thresholds'])
            self.flags = Accounts.Flags(data['flags'])
            self.balances = [Accounts.Balance(b) for b in data['balances']]
            self.signers = [Accounts.Signer(s) for s in data['signers']]
            self.data = [Accounts.Data({'key' : k, 'value' : v}) for k,v in data['data'].iteritems()]
            if 'inflation_destination' in data:
                self.inflation_destination = data['inflation_destination']
            else:
                self.inflation_destination = None

        def __repr__(self):
            return 'Account(id=%s,seq=%s,balances=%s)' % (self.account_id, self.sequence, self.balances)

    def __init__(self, accid):
        if not accid:
            raise ValueError('accid expected')
        self.accid = _address_to_account(accid)
        self.paginated = False
        self.streamed = False
        self.url = '/accounts/%s' % self.accid

    def _map2obj(self, data):
        return Accounts.Account(data)

    def transactions(self):
        """Returns fechable object for transactions associated with given account"""
        return Transactions._All(self.url)

    def operations(self):
        """Returns fechable object for operations associated with given account"""
        return Operations._All(self.url)

    def payments(self):
        """Returns fechable object for payments associated with given account"""
        return Payments._All(self.url)

    def offers(self):
        """Returns fechable object for offers associated with given account"""
        return Offers._Offers__All(self.url)

    def effects(self):
        """Returns fechable object for effects associated with given account"""
        return Effects._All(self.url)


class Transactions(Fetchable):
    class Transaction(object):
        """Transactin: https://www.stellar.org/developers/horizon/reference/resources/transaction.html"""
        def __init__(self, data):
            self.trxid = data['id']
            self.paging_token = data['paging_token']
            self.hash = data['hash']
            self.ledger = int(data['ledger'])
            self.account = data['source_account']
            self.account_seq = data['source_account_sequence']
            self.fee_paid = int(data['fee_paid'])
            self.operation_count = int(data['operation_count'])
            self.created_at = datetime.datetime.strptime(
                    data['created_at'], '%Y-%m-%dT%H:%M:%SZ')

            memo_type = data['memo_type']
            if memo_type == 'text':
                self.memo = (memo_type, data['memo'])
            elif memo_type == 'id':
                self.memo = (memo_type, int(data['memo']))
            elif memo_type in ['hash', 'return']:
                self.memo = (memo_type, binascii.hexlify(base64.b64decode(data['memo'])))
            else:
                self.memo = None

        def __repr__(self):
            return 'Transaction(id=%s,ledger=%s,account=%s,seq=%s)' % (self.trxid,\
                    self.ledger, _shorten_address(self.account), self.account_seq)

    def __init__(self, trxid):
        if not trxid:
            raise ValueError('transaction id required')
        self.trxid = trxid
        self.paginated = False
        self.streamed = False
        self.url = '/transactions/%s' % self.trxid

    def _map2obj(self, data):
        return Transactions.Transaction(data)

    def operations(self):
        """Returns fechable object for operations associated with given transaction"""
        return Operations._All(self.url)

    def payments(self):
        """Returns fechable object for payments associated with given transaction"""
        return Payments._All(self.url)

    def effects(self):
        """Returns fechable object for effects associated with given transaction"""
        return Effects._All(self.url)

    class _All(Fetchable):
        def __init__(self, baseurl=''):
            self.paginated = True
            self.streamed = True
            self.url = baseurl + '/transactions'

        def _map2obj(self, data):
            return Transactions.Transaction(data)


class Ledgers(Fetchable):
    class Ledger(object):
        """Ledger: https://www.stellar.org/developers/horizon/reference/resources/ledger.html"""
        def __init__(self, data):
            self.ledid = data['id']
            self.paging_token = data['paging_token']
            self.hash = data['hash']
            self.prev_hash = data['prev_hash']
            self.ledseq = int(data['sequence'])
            self.transaction_count = int(data['transaction_count'])
            self.operation_count = int(data['operation_count'])
            self.closed_at = datetime.datetime.strptime(
                    data['closed_at'], "%Y-%m-%dT%H:%M:%SZ")
            self.total_coins = data['total_coins']
            self.fee_pool = data['fee_pool']
            self.base_fee = int(data['base_fee'])
            self.base_reserve = data['base_reserve']
            self.max_tx_set_size = int(data['max_tx_set_size'])

        def __repr__(self):
            return 'Ledger(id=%s,ledseq=%s)' % (self.ledid, self.ledseq)

    def __init__(self, ledseq):
        if not ledseq:
            raise ValueError('ledger id expected')
        self.ledseq = ledseq
        self.paginated = False
        self.streamed = False
        self.url = '/ledgers/%s' % self.ledseq

    def _map2obj(self, data):
        return Ledgers.Ledger(data)

    def transactions(self):
        """Returns fechable object for transactions associated with given ledger"""
        return Transactions._All(self.url)

    def operations(self):
        """Returns fechable object for operations associated with given ledger"""
        return Operations._All(self.url)

    def payments(self):
        """Returns fechable object for payments associated with given ledger"""
        return Payments._All(self.url)

    def effects(self):
        """Returns fechable object for effects associated with given ledger"""
        return Effects._All(self.url)

    class _All(Fetchable):
        def __init__(self, baseurl=''):
            self.paginated = True
            self.streamed = True
            self.url = baseurl + '/ledgers'

        def _map2obj(self, data):
            return Ledgers.Ledger(data)


class Operations(Fetchable):
    class Operation(object):
        """Operation: https://www.stellar.org/developers/horizon/reference/resources/operation.html"""
        def __init__(self, data):
            self.opid = data['id']
            self.paging_token = data['paging_token']
            self.source_account = data['source_account']
            self.type = data['type']
            self.type_i = t = int(data['type_i'])
            self.created_at = datetime.datetime.strptime(
                    data['created_at'], "%Y-%m-%dT%H:%M:%SZ")
            self.transaction_hash = data['transaction_hash']

            if t == 0:
                self.account = data['account']
                self.funder = data['funder']
                self.starting_balance = data['starting_balance']
            elif t == 1:
                self.amount = data['amount']
                self.asset = Asset(data)
                self.from_account = data['from']
                self.to_account = data['to']
            elif t == 2:
                self.amount = data['amount']
                self.source_amount = data['source_amount']
                self.from_account = data['from']
                self.to_account = data['to']
                self.asset = Asset(data)
                self.send_asset = Asset(data, 'send_')
            elif t == 3:
                self.offer_id = data['offer_id']
                self.amount = data['amount']
                self.price = data['price']
                self.buying_asset = Asset(data, 'buying_')
                self.selling_asset = Asset(data, 'selling_')
            elif t == 4:
                self.amount = data['amount']
                self.price = data['price']
                self.buying_asset = Asset(data, 'buying_')
                self.selling_asset = Asset(data, 'selling_')
            elif t == 5:
                if 'low_threshold' in data:
                    self.low_threshold =  (True, data['low_threshold'])
                else:
                    self.low_threshold = (False, None)
                if 'med_threshold' in data:
                    self.med_threshold =  (True, data['med_threshold'])
                else:
                    self.med_threshold = (False, None)
                if 'high_threshold' in data:
                    self.high_threshold = (True, data['high_threshold'])
                else:
                    self.high_threshold = (False, None)
                if 'inflation_dest' in data:
                    self.inflation_dest = (True, data['inflation_dest'])
                else:
                    self.inflation_dest = (False, None)
                if 'home_domain' in data:
                    self.home_domain = (True, data['home_domain'])
                else:
                    self.home_domain = (False, None)
                if 'signer_key' in data:
                    self.signer_key = (True, data['signer_key'])
                else:
                    self.signer_key = (False, None)
                if 'signer_weight' in data:
                    self.signer_weight = (True, int(data['signer_weight']))
                else:
                    self.signer_weight = (False, None)
                if 'master_key_weight' in data:
                    self.master_key_weight = (True, int(data['master_key_weight']))
                else:
                    self.master_key_weight = (False, None)
                if 'set_flags' in data:
                    self.set_flags = (True, data['set_flags'])
                else:
                    self.set_flags = (False, None)
                if 'clear_flags' in data:
                    self.clear_flags = (True, data['clear_flags'])
                else:
                    self.clear_flags = (False, None)
            elif t == 6:
                self.trustor = data['trustor']
                self.trustee = data['trustee']
                self.asset = Asset(data)
            elif t == 7:
                self.trustor = data['trustor']
                self.trustee = data['trustee']
                self.asset = Asset(data)
                self.authorize = data['authorize']
            elif t == 8:
                self.account = data['account']
                self.merged_to = data['into']
            elif t == 9:
                pass
            elif t == 10:
                self.key = data['name']
                self.value = base64.b64decode(data['value'])
            else:
                raise Exception('Unsupported operation = %s' % self.type)

        def __repr__(self):
            return 'Operation(id=%s,account=%s,type=%s)' %\
                    (self.opid, _shorten_address(self.source_account), self.type)

    def __init__(self, opid):
        if not opid:
            raise ValueError('operation id expected')
        self.opid = opid 
        self.paginated = False
        self.streamed = False
        self.url = '/operations/%s' % self.opid

    def _map2obj(self, data):
            return Operations.Operation(data)

    def effects(self):
        """Returns fechable object for effects associated with given operation"""
        return Effects._All(self.url)

    class _All(Fetchable):
        def __init__(self, baseurl=''):
            self.paginated = True
            self.streamed = True
            self.url = baseurl + '/operations'

        def _map2obj(self, data):
            return Operations.Operation(data)

class Payments(object):
    class Payment(object):
        def __init__(self, data):
            self.pid = data['id']
            self.paging_token = data['paging_token']
            self.source_account = data['source_account']
            self.type = data['type']
            self.type_i = int(data['type_i'])
            self.created_at = datetime.datetime.strptime(
                    data['created_at'], "%Y-%m-%dT%H:%M:%SZ")
            self.transaction_hash = data['transaction_hash']
            if self.type_i == 0:
                self.amount = data['starting_balance']
                self.asset = native_asset
                self.destination = data['account']
            else:
                self.amount = data['amount']
                self.asset = Asset(data)
                self.destination = data['to']

        def __repr__(self):
            return 'Payment(%s,from=%s,to=%s,amount=%s,asset=%s)' %\
                    (self.type, _shorten_address(self.source_account),\
                    _shorten_address(self.destination), self.amount, self.asset)

    class _All(Fetchable):
        def __init__(self, baseurl=''):
            self.paginated = True
            self.streamed = True
            self.url = baseurl + '/payments'

        def _map2obj(self, data):
            return Payments.Payment(data)

class Effects(object):
    class Effect(object):
        def __init__(self, data):
            self.effectid = data['id']
            self.paging_token = data['paging_token']
            self.account = data['account']
            self.type = data['type']
            self.type_i = t = data['type_i']
            if t == 0:
                self.starting_balance = data['starting_balance']
            elif t == 1:
                pass
            elif t == 2 or t == 3:
                self.amount = data['amount']
                self.asset = Asset(data)
            elif t == 4:
                self.thresholds = Accounts.Thresholds(data)
            elif t == 5:
                self.home_domain = data['home_domain']
            elif t == 6:
                if 'auth_required_flag' in data:
                    self.auth_required = (True, data['auth_required_flag'])
                else:
                    self.auth_required = (False, None)
                if 'auth_revokable_flag' in data:
                    self.auth_revokable = (True, data['auth_revokable_flag'])
                else:
                    self.auth_revokable = (False, None)
            elif t == 10 or t == 11 or t == 12:
                self.weight = data['weight']
                self.public_key = data['public_key']
            elif t == 20 or t == 21 or t == 22:
                self.trustlimit = data['limit']
                self.trustasset = Asset(data)
            elif t == 23 or t == 24:
                self.trustor = data['trustor']
                self.asset_type = data['asset_type']
                self.asset_code = data['asset_code']
            elif t == 30 or t == 31 or t == 32:
                pass
            elif t == 33:
                self.seller = data['seller']
                self.offer_id = data['offer_id']
                self.sold_amount = data['sold_amount']
                self.sold_asset = Asset(data, 'sold_')
                self.bought_amount = data['bought_amount']
                self.bought_asset = Asset(data, 'bought_')
            elif t == 40:
                pass
            else:
                raise Exception('type not supported = %s' % self.type)

        def __repr__(self):
            return 'Effect(%s,%s,%s)' % (self.effectid,\
                    _shorten_address(self.account), self.type)


    class _All(Fetchable):
        def __init__(self, baseurl=''):
            self.paginated = True
            self.streamed = True
            self.url = baseurl + '/effects'

        def _map2obj(self, data):
            return Effects.Effect(data)

class Offers(Fetchable):
    class Offer(object):
        def __init__(self, data):
            self.offerid = data['id']
            self.paging_token = data['paging_token']
            self.seller = data['seller']
            self.selling = Asset(data['selling'])
            self.buying = Asset(data['buying'])
            self.amount = data['amount']
            self.price_r = (int(data['price_r']['n']), int(data['price_r']['d']))
            self.price = data['price']

        def __repr__(self):
            return 'Offer(%s,%s,%s,%s)' % (self.offerid, _shorten_address(self.seller),\
                    self.selling.asset_code, self.buying.asset_code)

    class __All(Fetchable):
        def __init__(self, baseurl=''):
            self.paginated = True
            self.streamed = False
            self.url = baseurl + '/offers'

        def _map2obj(self, data):
            return Offers.Offer(data)

        def stream(self):
            raise Exception('Stream not supported')

class Orderbooks(object):
    class Orderbook(object):
        def __init__(self, data):
            self.base_asset = Asset(data['base'])
            self.counter_asset = Asset(data['counter'])
            self.asks = []
            self.bids =  []
            for a in data['asks']:
                self.asks += [(
                    a['amount'],
                    (a['price_r']['n'], a['price_r']['d']),
                    a['price'],
                    )]
            for b in data['bids']:
                self.bids += [(
                    b['amount'],
                    (b['price_r']['n'], b['price_r']['d']),
                    b['price'],
                    )]

        def __repr__(self):
            return 'Orderbook(base=%s,counter=%s)' % (self.base_asset, self.counter_asset)

    class _All(Fetchable):
        def __init__(self, selling, buying):
            self.paginated = False
            self.streamed = False
            self.url = '/order_book?%s&%s' %\
                    (Asset.format_url_parameters(selling, 'selling_'), 
                            Asset.format_url_parameters(buying, 'buying_'))

        def _map2obj(self, data):
            return Orderbooks.Orderbook(data)

class Assets(object):
    class AssetDetails(object):
        def __init__(self, data):
            self.asset = Asset(data)
            self.paging_token = data['paging_token']
            self.num_accounts = data['num_accounts']
            self.amount = data['amount']
            self.flags = Accounts.Flags(data['flags'])
            self.toml = data['_links']['toml']['href']

        def __repr__(self):
            return str(self.asset)

    class _All(Fetchable):
        def __init__(self, asset_code, asset_issuer):
            self.paginated = True
            self.streamed = False
            self.url = '/assets?'
            if asset_code:
                self.url = '%sasset_code=%s&' % (self.url, asset_code)
            if asset_issuer:
                self.url = '%sasset_issuer=%s&' % (self.url, asset_issuer)
            self.url = self.url[:-1]

        def _map2obj(self, data):
            return Assets.AssetDetails(data)

class PaymentPaths(object):
    class PaymentPath(object):
        def __init__(self, data):
            self.source_asset_type = data['source_asset_type']
            if self.source_asset_type != 'native':
                self.source_asset_code = data['source_asset_code']
                self.source_asset_issuer = data['source_asset_issuer']
            self.source_amount = data['source_amount']
            self.destination_asset_type = data['destination_asset_type']
            if self.destination_asset_type != 'native':
                self.destination_asset_code = data['destination_asset_code']
                self.destination_asset_issuer = data['destination_asset_issuer']
            self.destination_amount = data['destination_amount']
            self.path = []
            for p in data['path']:
                self.path += [Asset(p)]

        def __repr__(self):
            return 'PaymentPath(src=%s,dest=%s,path=%s)' % (self.source_asset_type,\
                    self.destination_asset_type,self.path)

    def __init__(self, data):
        self.records = [PaymentPaths.PaymentPath(r) for r in data['_embedded']['records']]

    class _All(Fetchable):
        def __init__(self, from_account, to_account, to_asset, amount):
            self.paginated = False
            self.streamed = False
            self.url = '/paths?source_account=%s&destination_account=%s&%s&destination_amount=%s'\
                    % (from_account, to_account,
                            Asset.format_url_parameters(to_asset, 'destination_'), amount)

        def _map2obj(self, data):
            return PaymentPaths(data)

class NewTransaction(object):
    def __init__(self, account, signers, seq, fee, memo, time_bounds):
        self.account = account
        '''account on which transaction will be executed'''
        self.signers = signers
        '''signers of the transaction. if account is not secret, key then signers must be provided'''
        self.seq = seq
        '''sequence of the transaction'''
        self.fee = fee
        '''fee for the transaction'''
        self.memo = memo
        '''memo of the transaction'''
        self.time_bounds = time_bounds
        self.ops = []
        '''operations in transaction'''
        self.set_options_op = {}

        if len(signers) == 0 and account.startswith('G'):
            raise ValueError('signer(s) missing')
        elif len(signers) == 0 and account.startswith('S'):
            self.signers = [account]

        if self.account.startswith('S'):
            self.account = account_from_secret(account)

        self.account = _address_to_account(self.account)

    def __enter__(self):
        return self
	
    def __exit__(self, *args):
        self.submit()

    def submit(self):
        """Submits transaction to network. """
        account_seq = self.seq if self.seq else (int(account(self.account).fetch().sequence) + 1)

        self.__add_set_options_op()

        base_fee = self.fee if self.fee else BASE_FEE*len(self.ops)
        time_bounds = [XDR.time_bounds_to_xdr(self.time_bounds)] if self.time_bounds else []

        xdr = Xdr.nullclass()
        xdr.v = 0
        trxxdr = Xdr.types.Transaction(
                XDR.address_to_xdr(self.account), 
                base_fee, 
                account_seq,
                time_bounds,
                XDR.memo_to_xdr(self.memo), 
                self.ops,
                xdr)

        trxtypepacker = Xdr.StellarXDRPacker()
        trxtypepacker.pack_EnvelopeType(Xdr.const.ENVELOPE_TYPE_TX)
        trxtype = trxtypepacker.get_buffer()

        trxpacker = Xdr.StellarXDRPacker()
        trxpacker.pack_Transaction(trxxdr)
        trx = trxpacker.get_buffer()

        trx_hash = hashlib.sha256(network_id + trxtype + trx).digest()

        signatures = []
        for signer in self.signers:
            signatures += [_sign_trx_hash(signer, trx_hash)]

        tre = Xdr.types.TransactionEnvelope(trxxdr, signatures)

        txpacker = Xdr.StellarXDRPacker()
        txpacker.pack_TransactionEnvelope(tre)

        payload = base64.b64encode(txpacker.get_buffer())

        res = HTTP.post(horizon + '/transactions/', {'tx': payload })
        if 'status' in res:
            self.status = res['status']
            self.error = res['title']
            if 'extras' in res and 'result_codes' in res['extras']:
                result_codes = res['extras']['result_codes']
                self.transaction_error = result_codes['transaction']\
                        if 'transaction' in result_codes else ''
                self.operation_errors = result_codes['operations']\
                        if 'operations' in result_codes else []
            else:
                self.transaction_error = ''
                self.operation_errors = []
        else:
            self.status = 0
            self.trxid = res['hash']
            self.ledid = res['ledger']

        return self

    def is_success(self):
        """Returns whether transaction was successful after submitting to network """
        return True if self.status == 0 else False

    def result(self):
        """If transaction was successful then (transaction-id, ledger-id) pair"""
        if self.is_success():
            return (self.trxid, self.ledid)
        else:
            raise Exception('Transaction failed. Check errors()')

    def errors(self):
        """If transaction was not successful then (transaction-error, list-of operation error) pair"""
        if self.is_success():
            raise Exception('Transaction succeeded. Check result()')
        else:
            return (self.error, self.transaction_error, self.operation_errors)

    def create_account(self, account, starting_balance):
        """Creates account with given starting balance
        """
        account = _address_to_account(account)

        body = Xdr.nullclass()
        body.type = Xdr.const.CREATE_ACCOUNT
        body.createAccountOp = Xdr.types.CreateAccountOp(
                XDR.address_to_xdr(account),
                XDR.amount_to_xdr(starting_balance))
        self.ops += [Xdr.types.Operation([XDR.address_to_xdr(self.account)], body)]

        return self

    def pay(self, account, amount, asset='native'):
        """Pays given account with given amount of specified asset.
        asset can be 'native' or tuple in format (asset_code, asset_issuer).
        """
        account = _address_to_account(account)

        body = Xdr.nullclass()
        body.type = Xdr.const.PAYMENT
        body.paymentOp = Xdr.types.PaymentOp(
                XDR.address_to_xdr(account),
                XDR.asset_to_xdr(asset),
                XDR.amount_to_xdr(amount))
        self.ops += [Xdr.types.Operation([XDR.address_to_xdr(self.account)], body)]

        return self

    def pathpay(self, destination, dest_amount, dest_asset, max_send, send_asset, path):
        """Does the pathpay operation for given destination account, for dest_amount of dest_asset.
        It will send send_amount of send_asset upto max of max_send. Optionally path containing
        asset for intermediate exchanges can be specified (those path asset can be 'native' or 
        tuple in format (asset_code, asset_issuer).
        """
        destination = _address_to_account(destination)

        pathxdr = []
        #XXX is this tested?
        for p in path:
            pathxdr += [XDR.asset_to_xdr(p)]

        body = Xdr.nullclass()
        body.type = Xdr.const.PATH_PAYMENT
        body.pathPaymentOp = Xdr.types.PathPaymentOp(
                XDR.asset_to_xdr(send_asset),
                XDR.amount_to_xdr(max_send),
                XDR.address_to_xdr(destination),
                XDR.asset_to_xdr(dest_asset),
                XDR.amount_to_xdr(dest_amount),
                pathxdr)
        self.ops += [Xdr.types.Operation([XDR.address_to_xdr(self.account)], body)]

        return self

    def add_offer(self, sell_amount, sell_asset, buy_asset, price):
        """Adds offer of sell_amount for selling asset sell_asset, to buy buy_asset at given price. 
        sell_asset, buy_asset are asset in 'native' or tuple in format (asset_code, asset_issuer).
        price in (numerator, denominator) format. To buy 1 BTC at 100 XLM price would be (1, 100)
        """
        return self.update_offer(0, sell_amount, sell_asset, buy_asset, price)

    def add_passive_offer(self, sell_amount, sell_asset, buy_asset, price):
        """Creates passive offer of sell_amount for selling asset sell_asset, to buy buy_asset at given price. 
        sell_asset, buy_asset are asset in 'native' or tuple in format (asset_code, asset_issuer).
        price in (numerator, denominator) format. To buy 1 BTC at 100 XLM price would be (1, 100)
        """
        body = Xdr.nullclass()
        body.type = Xdr.const.CREATE_PASSIVE_OFFER
        body.createPassiveOfferOp = Xdr.types.CreatePassiveOfferOp(
                XDR.asset_to_xdr(sell_asset),
                XDR.asset_to_xdr(buy_asset),
                XDR.amount_to_xdr(sell_amount),
                XDR.price_to_xdr(price))
        self.ops += [Xdr.types.Operation([XDR.address_to_xdr(self.account)], body)]

        return self

    def update_offer(self, offer_id, sell_amount, sell_asset, buy_asset, price):
        """Updates offer with given offer_id with specified details.
        sell_asset, buy_asset are asset in 'native' or tuple in format (asset_code, asset_issuer).
        price in (numerator, denominator) format. To buy 1 BTC at 100 XLM price would be (1, 100)
        """
        body = Xdr.nullclass()
        body.type = Xdr.const.MANAGE_OFFER
        body.manageOfferOp = Xdr.types.ManageOfferOp(
                XDR.asset_to_xdr(sell_asset),
                XDR.asset_to_xdr(buy_asset),
                XDR.amount_to_xdr(sell_amount),
                XDR.price_to_xdr(price),
                offer_id)
        self.ops += [Xdr.types.Operation([XDR.address_to_xdr(self.account)], body)]

        return self

    def remove_offer(self, offer_id, sell_asset, buy_asset):
        """Removes existing offer with given offer_id of sell_asset <-> buy_asset trade
        """
        return self.update_offer(offer_id, "0", sell_asset, buy_asset, (1,1))

    def set_inflation_destination(self, account):
        """Sets the inflation of given account (SET_OPTIONS operation)"""
        self.set_options_op['inflation'] = account

        return self

    def set_flags(self, auth_required=False, auth_revocable=False, auth_immutable=False):
        """Sets the auth flags of the given account (SET_OPTIONS operation)"""
        auth_flags = 0
        if auth_required or auth_revocable or auth_immutable:
            if auth_required:
                auth_flags += 1
            if auth_revocable:
                auth_flags += 2
            if auth_immutable:
                auth_flags += 4
            self.set_options_op['set_flags'] = auth_flags

        return self

    def clear_flags(self, auth_required=False, auth_revocable=False, auth_immutable=False):
        """Clear auth flags of the given account (SET_OPTIONS operation)"""
        auth_flags = 0
        if auth_required or auth_revocable or auth_immutable:
            if auth_required:
                auth_flags += 1
            if auth_revocable:
                auth_flags += 2
            if auth_immutable:
                auth_flags += 4
            self.set_options_op['clear_flags'] = auth_flags

        return self
	
    def set_thresholds(self, high=None, medium=None, low=None):
        """Sets threshold of given account (SET_OPTIONS operation)"""
        if high or medium or low:
            if high:
                self.set_options_op['high'] = high
            if medium:
                self.set_options_op['medium'] = medium
            if low:
                self.set_options_op['low'] = low

        return self

    def set_master_weight(self, weight):
        """Sets master weight of the given account (SET_OPTIONS operation)"""
        self.set_options_op['master_weight'] = weight
        return self

    def set_signer(self, signer_type, key, weight):
        """
        Sets sigers of the given account (SET_OPTIONS operation).
        available signer_type are ('ed25519PublicKey','hashX','preAuthTx')
        """
        self.set_options_op['signer'] = (signer_type, key, weight)
        return self
	
    def set_home_domain(self, domain):
        """Sets home domain of the given account (SET_OPTIONS operation)"""
        self.set_options_op['home_domain'] = domain;
        return self

    def __add_set_options_op(self):
        if len(self.set_options_op) > 0:
            toarray = lambda m, x : [] if x not in m else [m[x]]

            inflation_destination_ = [] if 'inflation' not in self.set_options_op\
                    else [XDR.address_to_xdr(self.set_options_op['inflation'])]
            set_flags_ = toarray(self.set_options_op, 'set_flags')
            clear_flags_ = toarray(self.set_options_op, 'clear_flags')
            high_ = toarray(self.set_options_op, 'high')
            medium_ = toarray(self.set_options_op, 'medium')
            low_ = toarray(self.set_options_op, 'low')
            master_weight_ = toarray(self.set_options_op, 'master_weight')
            signer_ = toarray(self.set_options_op, 'signer')
            if len(signer_) > 0:
                signer_ = signer_[0]
                signer_ = [XDR.signer_to_xdr(signer_[0], signer_[1], signer_[2])]
            home_domain_ = toarray(self.set_options_op, 'home_domain')

            body = Xdr.nullclass()
            body.type = Xdr.const.SET_OPTIONS
            body.setOptionsOp = Xdr.types.SetOptionsOp(
                    inflation_destination_,
                    clear_flags_, set_flags_,
                    master_weight_,
                    low_, medium_, high_,
                    home_domain_,
                    signer_)
            self.ops += [Xdr.types.Operation([XDR.address_to_xdr(self.account)], body)]

    def create_or_update_trust(self, asset, limit):
        """Creates or update trust for given asset with specified limit.
        asset is tuple in format (asset_code, asset_issuer) or 'native'.
        limit is amount indicating limit of given asset
        """
        body = Xdr.nullclass()
        body.type = Xdr.const.CHANGE_TRUST
        body.changeTrustOp = Xdr.types.ChangeTrustOp(
                XDR.asset_to_xdr(asset),
                XDR.amount_to_xdr(limit))
        self.ops += [Xdr.types.Operation([XDR.address_to_xdr(self.account)], body)]

        return self

    def remove_trust(self, asset):
        """Remove trust for given asset. 
        asset is tuple in format (asset_code, asset_issuer) or 'native'.
        """
        return self.create_or_update_trust(asset, "0")

    def __perform_trust_op(self, account, asset_code, is_allow):
        body = Xdr.nullclass()
        body.type = Xdr.const.ALLOW_TRUST
        body.allowTrustOp = Xdr.types.AllowTrustOp(
                XDR.address_to_xdr(account),
                XDR.assetcode_to_xdr(asset_code),
                is_allow)
        self.ops += [Xdr.types.Operation([XDR.address_to_xdr(self.account)], body)]

        return self

    def authorize_trust(self, account, asset_code):
        """Authorize given account to perform transaction for given asset_code. """
        account = _address_to_account(account)

        return self.__perform_trust_op(account, asset_code, True)
       
    def deauthorize_trust(self, account, asset_code):
        """Deauthorize given account to perform transaction for given asset_code. """
        account = _address_to_account(account)

        return self.__perform_trust_op(account, asset_code, False)

    def merge_this_account_with(self, account):
        """Merges current account with input account"""
        account = _address_to_account(account)

        body = Xdr.nullclass()
        body.type = Xdr.const.ACCOUNT_MERGE
        body.destination = XDR.address_to_xdr(account)
        self.ops += [Xdr.types.Operation([XDR.address_to_xdr(self.account)], body)]

        return self

    def run_inflation(self):
        """Runs inflation process with this account """
        body = Xdr.nullclass()
        body.type = Xdr.const.INFLATION
        self.ops += [Xdr.types.Operation([XDR.address_to_xdr(self.account)], body)]

        return self

    def put_or_update_data(self, key, value):
        """Puts the key value pair if not already present. If key is already presents
        then updates old value with input value.
        """
        key = bytearray(key, encoding='utf-8')
        value = [bytearray(value, encoding='utf-8')] if value else []

        body = Xdr.nullclass()
        body.type = Xdr.const.MANAGE_DATA
        body.manageDataOp = Xdr.types.ManageDataOp(key, value)
        self.ops += [Xdr.types.Operation([XDR.address_to_xdr(self.account)], body)]

        return self

    def remove_data(self, key):
        """Removes the key value pair associated with given input key"""
        return self.put_or_update_data(key, None)

def account(accid):
    """
    Returns Fetchable object to retrieve account details of the accid.
    You can chain other operations e.g. stellar.account(accid).operations() 
    to retrieve operations of the given account.

        a = stellar.account('GAEE..IB4V..').fetch() 
        a_ops = stellar.account('GAEE..IB4V..').
                    operations().fetch().entries() 
    """
    return Accounts(accid)

def transactions():
    """
    Returns transactions thats are being submitted 
    to stellar network.

        ts = stellar.transactions().fetch(
                    limit=5, order='desc').entries()
    """
    return Transactions._All()

def transaction(trxid):
    """
    Returns single transaction with given trxid. Can be chained to retrieve
    other details of the given transactions such as all operations in given
    transaction etc.

        t = stellar.transaction('aefe__b781__').fetch()
        t_ops = stellar.transaction('aefe__b781__')
                    .operations().fetch().entries()
    """
    return Transactions(trxid)

def ledgers():
    """
    Returns ledgers that are being processed be 
    on stellar network.

        ls = stellar.ledgers().fetch(
                        cursor=15, order='asc').entries()
    """
    return Ledgers._All()

def ledger(ledseq):
    """
    Returns single ledger with given ledseq. Can be chained to retreive other
    details such as transactions that are part of given ledger.

        l = stellar.ledger(12345).fetch()
    """
    return Ledgers(ledseq);

def effects():
    """
    Returns all the effets that are being performed 
    on stellar network.

        es = stellar.effects().fetch()
    """
    return Effects._All()

def operations():
    """
    Returns all the operaion that are being performed 
    on stellar network.

        ops = stellar.operations().fetch(
                        limit=5, order='desc')
    """
    return Operations._All()

def operation(opid):
    """
    Returns single opreation with given opid
    to be fetched from stellar network.

        o = stellar.operation('28551568194277377').fetch()
        o_effs = stellar.operation('28551568194277377').
                    effects().fetch().entries()
    """
    return Operations(opid);

def payments():
    """
    Returns all the payment operation that are done 
    on stellar network.

        ps = stellar.payments().fetch().entries()
    """
    return Payments._All()

def trades(buying, selling):
    """Returns all the trade where buying <-> selling assets are being traded.
    Curently stellar network always returns resource not found for this query.
    """
    raise NotImplementedError

def find_payment_path(from_account, to_account, to_asset, amount):
    """
    A path payment specifies a series of assets to route a payment through
    from source asset (the asset debited from the payer) to destination asset 
    (the asset credited to the payee). As part of the search, horizon will load
    a list of assets available to the source account id and will find any payment 
    paths from those source assets to the desired destination asset. The search’s 
    amount parameter will be used to determine if there a given path can satisfy 
    a payment of the desired amount. 

        path = stellar.find_payment_path('GAEE__ADED__',
                'GDAA__3EFD__', ('USD', 'GDKG__GZ2O__'),
                "10.1").fetch()
    """
    return PaymentPaths._All(from_account, to_account, to_asset, amount)

def assets(asset_code=None, asset_issuer=None):
    """
    Returns all the assets. Optionally assets can be filtered based on asset_code
    or asset_issuer.

        usds = stellar.assets(asset_code='USD').fetch().entries()
    """
    return Assets._All(asset_code, asset_issuer)

def orderbook(buying, selling):
    """
    All the pending offers where people are 'buying' asset in exchange of
    'selling' asset.

        book = stellar.orderbook(selling=('AST1', 'GAEE__ADED__'),
                buying=('AST2', 'GDAA__3EFD__')).fetch().entries()
    """
    return Orderbooks._All(buying, selling)

def new_transaction(account, signers=[], seq=None, fee=None, memo=None, time_bounds=[]):
    """
    Creates new transaction.
    account - can be public key or secret. If account is self signed then
    secret of the account is sufficient. Otherwise public key in account parameter
    and signers must have secrets of the necessary signers of that account.
    seq - sequence of transaction(int), if not given will get last sequence and increment by one
    fee - fee(int), if given, will be used instead of default fee of 100 stroops/op.
    memo - optional text memo in string format or tuple (memo_type, memo_data) for other formats. 
           available other formats are ('id', 'hash', 'return')
    time_bounds - if given, upper and lower bounds for the transaction to be effective.

    Can be used with with-statement as follows:

        with new_transaction(account, memo='double payment') as t:
            t.pay(destination1, amount1)
            t.pay(destination2, amount2)

    This will autmoatically submit the transaction when with-statement completes.

    Each operation in transaction costs atleast a base fee (which is 100 stroops).
    So if you submit 5 different operations in single transaction it will cost you
    atleast 500 stroops. Only exception are set_options operation. So if you 
    set inflation destination and auth flags in single transaction then it will only
    cost you 100 stroops. 
    """
    return NewTransaction(account, signers, seq, fee, memo, time_bounds)
