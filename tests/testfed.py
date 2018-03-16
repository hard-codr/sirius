import stellar
import stellar.utils
import requests
from mock import patch, call

result = { 'hash' : 'cafebabe', 'ledger' : '42' }
acc = { 
        "id" : "GDZ4R34MNVITLNZ4KVKBEANJU3UZZFZZLOX7ZVU5AWI7FEL5A6JWDM24",
        "paging_token": "",
        "account_id": "GDZ4R34MNVITLNZ4KVKBEANJU3UZZFZZLOX7ZVU5AWI7FEL5A6JWDM24",
        "sequence": "28515645087809560",
        "subentry_count": 1,
        "inflation_destination": "",
        "thresholds": {
            "low_threshold": 1,
            "med_threshold": 1,
            "high_threshold": 1
            },
        "flags": {
            "auth_required": True,
            "auth_revocable": False
            },
        "balances": [
            {
                "balance": "9999.9999900",
                "asset_type": "native"
                }
            ],
        "signers": [
            {
                "public_key": "GDZ4R34MNVITLNZ4KVKBEANJU3UZZFZZLOX7ZVU5AWI7FEL5A6JWDM24",
                "weight": 42,
                "key": "GDZ4R34MNVITLNZ4KVKBEANJU3UZZFZZLOX7ZVU5AWI7FEL5A6JWDM24",
                "type": "ed25519_public_key"
                },
            ],
        "data" : {}
        }

stellar.setup_test_network()

def test_resolve_to_account():
    class MockResponse(object):
        def __init__(self, status_code, lines=None, json=None):
            self.status_code = status_code 
            self.lines = lines
            self.jsondict = json

        def iter_lines(self):
            for line in self.lines:
                    yield line
            raise StopIteration

        def json(self):
            return self.jsondict

    def mock_get(req):
        if req.endswith('stellar.toml'):
            return MockResponse(200, ["FEDERATION_SERVER = \"https://stellar.org/federation\""])
        elif req.endswith('type=name'):
            return MockResponse(200, json={'account_id' : 'GDZ4R34MNVITLNZ4KVKBEANJU3UZZFZZLOX7ZVU5AWI7FEL5A6JWDM24'})
        raise Exception('Unexpected req = %s' % req)

    with patch.object(requests, 'get') as get_mock:
        get_mock.side_effect = mock_get
        acc = stellar.utils.FED.resolve_to_account('address*stellar.org')
        assert acc == 'GDZ4R34MNVITLNZ4KVKBEANJU3UZZFZZLOX7ZVU5AWI7FEL5A6JWDM24'

    calls = [
            call('https://stellar.org/.well-known/stellar.toml'),
            call('https://stellar.org/federation?q=address*stellar.org&type=name')
            ]
    get_mock.assert_has_calls(calls)

    with patch.object(requests, 'get') as get_mock_1:
        get_mock_1.side_effect = mock_get
        acc = stellar.utils.FED.resolve_to_account('address@email.com*stellar.org')
        assert acc == 'GDZ4R34MNVITLNZ4KVKBEANJU3UZZFZZLOX7ZVU5AWI7FEL5A6JWDM24'

    calls_1 = [
            call('https://stellar.org/.well-known/stellar.toml'),
            call('https://stellar.org/federation?q=address@email.com*stellar.org&type=name')
            ]
    get_mock_1.assert_has_calls(calls_1)


def test_fed_create_account():
    trx_env = 'AAAAAGxfNmJ5gxclDy95e+IrnQwRrW6LyjVwpoQ2iKOT684jAAAAZABlTtQAAAAZAAAAAAAAAAAAAAABAAAAAQAAAABsXzZieYMXJQ8veXviK50MEa1ui8o1cKaENoijk+vOIwAAAAAAAAAA88jvjG1RNbc8VVQSAamm6ZyXOVuv/NadBZHykX0Hk2EAAAAAO5rKAAAAAAAAAAABk+vOIwAAAEAXazw4qM/rzuDpw4+cLbuHrPhM6Ugq5FSEfRVTwHQ20baNlf2PEW+5acvXn2ntI5U2KXbUxgvUgGGs3U5rgpIO'
    account = 'GDZ4R34MNVITLNZ4KVKBEANJU3UZZFZZLOX7ZVU5AWI7FEL5A6JWDM24'

    with patch.object(stellar.utils.HTTP, 'post', return_value=result) as get_mock:
        with patch.object(stellar.utils.HTTP, 'get', return_value=acc) as acc_mock:
            with patch.object(stellar.utils.FED, 'resolve_to_account', return_value=account) as fed_mock:
                with stellar.new_transaction('SALCB22A3PL2JFI3GE62BM4S2TE64NJZP4GF2DBGPBC6QIUQ7GI7BRBN') as t:
                    t.create_account('hardcodr*stellar.org', '100')

    get_mock.assert_called_once_with('https://horizon-testnet.stellar.org/transactions/', { 'tx' : trx_env })
    acc_mock.assert_called_once()
    fed_mock.assert_called_once_with('hardcodr*stellar.org')
    assert t.is_success()
    assert t.result() == ('cafebabe', '42')

def test_fed_pay():
    trx_env_native = 'AAAAAGxfNmJ5gxclDy95e+IrnQwRrW6LyjVwpoQ2iKOT684jAAAAZABlTtQAAAAZAAAAAAAAAAAAAAABAAAAAQAAAABsXzZieYMXJQ8veXviK50MEa1ui8o1cKaENoijk+vOIwAAAAEAAAAA88jvjG1RNbc8VVQSAamm6ZyXOVuv/NadBZHykX0Hk2EAAAAAAAAAADuaygAAAAAAAAAAAZPrziMAAABAEyOA0c4Ia9CtyBY7+sjaoR0VUKdZxXRv1p/uRsGx+lR0iXOjYW/qQuUCI7tOdfh8btSRpJ/njwAlzOZ1Jn4DAw=='

    trx_env_non_native = 'AAAAAGxfNmJ5gxclDy95e+IrnQwRrW6LyjVwpoQ2iKOT684jAAAAZABlTtQAAAAZAAAAAAAAAAAAAAABAAAAAQAAAABsXzZieYMXJQ8veXviK50MEa1ui8o1cKaENoijk+vOIwAAAAEAAAAA88jvjG1RNbc8VVQSAamm6ZyXOVuv/NadBZHykX0Hk2EAAAABQ09EUgAAAADpY3RZ9hLbOfAO9jcq1bSadILPs6jQEDWbPwin3mmLggAAAAA7msoAAAAAAAAAAAGT684jAAAAQCiC1F24byWXlgxj4I/uw8faz0IbWe6nVZvk1zIQdliUMSApDi/47tExLIP36K/Kyj4hL+ilRjkAUBttVwkYZAk='

    account = 'GDZ4R34MNVITLNZ4KVKBEANJU3UZZFZZLOX7ZVU5AWI7FEL5A6JWDM24'

    with patch.object(stellar.utils.HTTP, 'post', return_value=result) as get_mock:
        with patch.object(stellar.utils.HTTP, 'get', return_value=acc) as acc_mock:
            with patch.object(stellar.utils.FED, 'resolve_to_account', return_value=account) as fed_mock:
                with stellar.new_transaction('SALCB22A3PL2JFI3GE62BM4S2TE64NJZP4GF2DBGPBC6QIUQ7GI7BRBN') as t:
                    t.pay('hardcodr*stellar.org', '100')

    get_mock.assert_called_once_with('https://horizon-testnet.stellar.org/transactions/', { 'tx' : trx_env_native })
    acc_mock.assert_called_once()
    fed_mock.assert_called_once_with('hardcodr*stellar.org')
    assert t.is_success()
    assert t.result() == ('cafebabe', '42')

    with patch.object(stellar.utils.HTTP, 'post', return_value=result) as get_mock_1:
        with patch.object(stellar.utils.HTTP, 'get', return_value=acc) as acc_mock_1:
            with patch.object(stellar.utils.FED, 'resolve_to_account', return_value=account) as fed_mock_1:
                with stellar.new_transaction('SALCB22A3PL2JFI3GE62BM4S2TE64NJZP4GF2DBGPBC6QIUQ7GI7BRBN') as t:
                    t.pay('hardcodr*stellar.org', '100', asset=('CODR', 'GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ'))

    get_mock_1.assert_called_once_with('https://horizon-testnet.stellar.org/transactions/', { 'tx' : trx_env_non_native })
    acc_mock_1.assert_called_once()
    fed_mock_1.assert_called_once_with('hardcodr*stellar.org')
    assert t.is_success()
    assert t.result() == ('cafebabe', '42')


def test_fed_path_payment():
    trx_env = 'AAAAAGxfNmJ5gxclDy95e+IrnQwRrW6LyjVwpoQ2iKOT684jAAAAZABlTtQAAAAZAAAAAAAAAAAAAAABAAAAAQAAAABsXzZieYMXJQ8veXviK50MEa1ui8o1cKaENoijk+vOIwAAAAIAAAACU1JDQVNTRVQAAAAAAAAAAOljdFn2Ets58A72NyrVtJp0gs+zqNAQNZs/CKfeaYuCAAAAADuaygAAAAAA88jvjG1RNbc8VVQSAamm6ZyXOVuv/NadBZHykX0Hk2EAAAACREVTVEFTU0VUAAAAAAAAAOljdFn2Ets58A72NyrVtJp0gs+zqNAQNZs/CKfeaYuCAAAAADuaygAAAAABAAAAAklOVEFTU0VUAAAAAAAAAADpY3RZ9hLbOfAO9jcq1bSadILPs6jQEDWbPwin3mmLggAAAAAAAAABk+vOIwAAAECSgtpCVj4SqV2J29PLLuMxvUm2icED1fX85P0W5A2mr9K2NYS6iCCjM2xAeCtM44UDEKgriObHu399lPTmt6oK'

    account = 'GDZ4R34MNVITLNZ4KVKBEANJU3UZZFZZLOX7ZVU5AWI7FEL5A6JWDM24'

    with patch.object(stellar.utils.HTTP, 'post', return_value=result) as get_mock:
        with patch.object(stellar.utils.HTTP, 'get', return_value=acc) as acc_mock:
            with patch.object(stellar.utils.FED, 'resolve_to_account', return_value=account) as fed_mock:
                with stellar.new_transaction('SALCB22A3PL2JFI3GE62BM4S2TE64NJZP4GF2DBGPBC6QIUQ7GI7BRBN') as t:
                    t.pathpay('hardcodr*stellar.org', 
                        '100', ('DESTASSET', 'GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ'),
                        '100', ('SRCASSET', 'GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ'), 
                        path=[('INTASSET', 'GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ')])

    get_mock.assert_called_once_with('https://horizon-testnet.stellar.org/transactions/', { 'tx' : trx_env })
    acc_mock.assert_called_once()
    fed_mock.assert_called_once_with('hardcodr*stellar.org')
    assert t.is_success()
    assert t.result() == ('cafebabe', '42')

def test_fed_set_inflation():
    trx_env = 'AAAAAGxfNmJ5gxclDy95e+IrnQwRrW6LyjVwpoQ2iKOT684jAAAAZABlTtQAAAAZAAAAAAAAAAAAAAABAAAAAQAAAABsXzZieYMXJQ8veXviK50MEa1ui8o1cKaENoijk+vOIwAAAAUAAAABAAAAAOljdFn2Ets58A72NyrVtJp0gs+zqNAQNZs/CKfeaYuCAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAZPrziMAAABA/1oRN7C7T/B4/d0vsRO3ZbFrNwdbPT5Qfy9hIGcbAgAhKXq/U/wB8cMHBi27rMlGOeTgfBO/IlemOmgnsuskBA=='

    account = 'GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ'

    with patch.object(stellar.utils.HTTP, 'post', return_value=result) as get_mock:
        with patch.object(stellar.utils.HTTP, 'get', return_value=acc) as acc_mock:
            with patch.object(stellar.utils.FED, 'resolve_to_account', return_value=account) as fed_mock:
                with stellar.new_transaction('SALCB22A3PL2JFI3GE62BM4S2TE64NJZP4GF2DBGPBC6QIUQ7GI7BRBN') as t:
                    t.set_inflation_destination('inflation*stellar.org')

    get_mock.assert_called_once_with('https://horizon-testnet.stellar.org/transactions/', { 'tx' : trx_env })
    acc_mock.assert_called_once()
    fed_mock.assert_called_once_with('inflation*stellar.org')
    assert t.is_success()
    assert t.result() == ('cafebabe', '42')

def test_fed_authorize_trust():
    trx_env = 'AAAAAGxfNmJ5gxclDy95e+IrnQwRrW6LyjVwpoQ2iKOT684jAAAAZABlTtQAAAAZAAAAAAAAAAAAAAABAAAAAQAAAABsXzZieYMXJQ8veXviK50MEa1ui8o1cKaENoijk+vOIwAAAAcAAAAA6WN0WfYS2znwDvY3KtW0mnSCz7Oo0BA1mz8Ip95pi4IAAAABQ09EUgAAAAEAAAAAAAAAAZPrziMAAABAl4QaeVgE2pVft3A6MAUtTdBTACiz247BSY4wFU8orFURt7X40j8TZIiXN+IH4zFtWceCgze655uE51uHcuGrCQ=='

    account = 'GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ'

    with patch.object(stellar.utils.HTTP, 'post', return_value=result) as get_mock:
        with patch.object(stellar.utils.HTTP, 'get', return_value=acc) as acc_mock:
            with patch.object(stellar.utils.FED, 'resolve_to_account', return_value=account) as fed_mock:
                with stellar.new_transaction('SALCB22A3PL2JFI3GE62BM4S2TE64NJZP4GF2DBGPBC6QIUQ7GI7BRBN') as t:
                    t.authorize_trust('issuee*stellar.org', 'CODR')

    get_mock.assert_called_once_with('https://horizon-testnet.stellar.org/transactions/', { 'tx' : trx_env })
    acc_mock.assert_called_once()
    fed_mock.assert_called_once_with('issuee*stellar.org')
    assert t.is_success()
    assert t.result() == ('cafebabe', '42')

def test_fed_deauthorize_trust():
    trx_env = 'AAAAAGxfNmJ5gxclDy95e+IrnQwRrW6LyjVwpoQ2iKOT684jAAAAZABlTtQAAAAZAAAAAAAAAAAAAAABAAAAAQAAAABsXzZieYMXJQ8veXviK50MEa1ui8o1cKaENoijk+vOIwAAAAcAAAAA6WN0WfYS2znwDvY3KtW0mnSCz7Oo0BA1mz8Ip95pi4IAAAABQ09EUgAAAAAAAAAAAAAAAZPrziMAAABAY4XKfczup7NrjvhH/sX7IpUVXm+OcXmlRux5gEI8rwTxmLOhjxnHuPQeOvis6bfv3+Qe/lNJlUPYtZffANKxBg=='

    account = 'GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ'

    with patch.object(stellar.utils.HTTP, 'post', return_value=result) as get_mock:
        with patch.object(stellar.utils.HTTP, 'get', return_value=acc) as acc_mock:
            with patch.object(stellar.utils.FED, 'resolve_to_account', return_value=account) as fed_mock:
                with stellar.new_transaction('SALCB22A3PL2JFI3GE62BM4S2TE64NJZP4GF2DBGPBC6QIUQ7GI7BRBN') as t:
                    t.deauthorize_trust('issuee*stellar.org', 'CODR')

    get_mock.assert_called_once_with('https://horizon-testnet.stellar.org/transactions/', { 'tx' : trx_env })
    acc_mock.assert_called_once()
    fed_mock.assert_called_once_with('issuee*stellar.org')
    assert t.is_success()
    assert t.result() == ('cafebabe', '42')

def test_account_merge():
    trx_env = 'AAAAAGxfNmJ5gxclDy95e+IrnQwRrW6LyjVwpoQ2iKOT684jAAAAZABlTtQAAAAZAAAAAAAAAAAAAAABAAAAAQAAAABsXzZieYMXJQ8veXviK50MEa1ui8o1cKaENoijk+vOIwAAAAgAAAAA6WN0WfYS2znwDvY3KtW0mnSCz7Oo0BA1mz8Ip95pi4IAAAAAAAAAAZPrziMAAABAZ7IsT17C1Lm1Jfy3zHAG7Adxw+7IfICtxkMgqybiQhUt19GpkiUy/osFyuK6207U8UsdH1+09tkiUvigLQfKAg=='

    account = 'GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ'

    with patch.object(stellar.utils.HTTP, 'post', return_value=result) as get_mock:
        with patch.object(stellar.utils.HTTP, 'get', return_value=acc) as acc_mock:
            with patch.object(stellar.utils.FED, 'resolve_to_account', return_value=account) as fed_mock:
                with stellar.new_transaction('SALCB22A3PL2JFI3GE62BM4S2TE64NJZP4GF2DBGPBC6QIUQ7GI7BRBN') as t:
                    t.merge_this_account_with('target*stellar.org')

    get_mock.assert_called_once_with('https://horizon-testnet.stellar.org/transactions/', { 'tx' : trx_env })
    acc_mock.assert_called_once()
    fed_mock.assert_called_once_with('target*stellar.org')
    assert t.is_success()
    assert t.result() == ('cafebabe', '42')
