import stellar
import stellar.utils
from mock import patch

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


def test_create_account():
    trx_env = 'AAAAAGxfNmJ5gxclDy95e+IrnQwRrW6LyjVwpoQ2iKOT684jAAAAZABlTtQAAAAZAAAAAAAAAAAAAAABAAAAAQAAAABsXzZieYMXJQ8veXviK50MEa1ui8o1cKaENoijk+vOIwAAAAAAAAAA88jvjG1RNbc8VVQSAamm6ZyXOVuv/NadBZHykX0Hk2EAAAAAO5rKAAAAAAAAAAABk+vOIwAAAEAXazw4qM/rzuDpw4+cLbuHrPhM6Ugq5FSEfRVTwHQ20baNlf2PEW+5acvXn2ntI5U2KXbUxgvUgGGs3U5rgpIO'

    with patch.object(stellar.utils.HTTP, 'post', return_value=result) as get_mock:
        with patch.object(stellar.utils.HTTP, 'get', return_value=acc) as acc_mock:
            with stellar.new_transaction('SALCB22A3PL2JFI3GE62BM4S2TE64NJZP4GF2DBGPBC6QIUQ7GI7BRBN') as t:
                t.create_account('GDZ4R34MNVITLNZ4KVKBEANJU3UZZFZZLOX7ZVU5AWI7FEL5A6JWDM24', '100')

    get_mock.assert_called_once_with('https://horizon-testnet.stellar.org/transactions/', { 'tx' : trx_env })
    acc_mock.assert_called_once() 
    assert t.is_success()
    assert t.result() == ('cafebabe', '42')

def test_pay():
    trx_env_native = 'AAAAAGxfNmJ5gxclDy95e+IrnQwRrW6LyjVwpoQ2iKOT684jAAAAZABlTtQAAAAZAAAAAAAAAAAAAAABAAAAAQAAAABsXzZieYMXJQ8veXviK50MEa1ui8o1cKaENoijk+vOIwAAAAEAAAAA88jvjG1RNbc8VVQSAamm6ZyXOVuv/NadBZHykX0Hk2EAAAAAAAAAADuaygAAAAAAAAAAAZPrziMAAABAEyOA0c4Ia9CtyBY7+sjaoR0VUKdZxXRv1p/uRsGx+lR0iXOjYW/qQuUCI7tOdfh8btSRpJ/njwAlzOZ1Jn4DAw=='

    trx_env_non_native = 'AAAAAGxfNmJ5gxclDy95e+IrnQwRrW6LyjVwpoQ2iKOT684jAAAAZABlTtQAAAAZAAAAAAAAAAAAAAABAAAAAQAAAABsXzZieYMXJQ8veXviK50MEa1ui8o1cKaENoijk+vOIwAAAAEAAAAA88jvjG1RNbc8VVQSAamm6ZyXOVuv/NadBZHykX0Hk2EAAAABQ09EUgAAAADpY3RZ9hLbOfAO9jcq1bSadILPs6jQEDWbPwin3mmLggAAAAA7msoAAAAAAAAAAAGT684jAAAAQCiC1F24byWXlgxj4I/uw8faz0IbWe6nVZvk1zIQdliUMSApDi/47tExLIP36K/Kyj4hL+ilRjkAUBttVwkYZAk='

    with patch.object(stellar.utils.HTTP, 'post', return_value=result) as get_mock:
        with patch.object(stellar.utils.HTTP, 'get', return_value=acc) as acc_mock:
            with stellar.new_transaction('SALCB22A3PL2JFI3GE62BM4S2TE64NJZP4GF2DBGPBC6QIUQ7GI7BRBN') as t:
                t.pay('GDZ4R34MNVITLNZ4KVKBEANJU3UZZFZZLOX7ZVU5AWI7FEL5A6JWDM24', '100')

    get_mock.assert_called_once_with('https://horizon-testnet.stellar.org/transactions/', { 'tx' : trx_env_native })
    acc_mock.assert_called_once() 
    assert t.is_success()
    assert t.result() == ('cafebabe', '42')

    with patch.object(stellar.utils.HTTP, 'post', return_value=result) as get_mock_1:
        with patch.object(stellar.utils.HTTP, 'get', return_value=acc) as acc_mock_1:
            with stellar.new_transaction('SALCB22A3PL2JFI3GE62BM4S2TE64NJZP4GF2DBGPBC6QIUQ7GI7BRBN') as t:
                t.pay('GDZ4R34MNVITLNZ4KVKBEANJU3UZZFZZLOX7ZVU5AWI7FEL5A6JWDM24', '100', 
                        asset=('CODR', 'GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ'))

    get_mock_1.assert_called_once_with('https://horizon-testnet.stellar.org/transactions/', { 'tx' : trx_env_non_native })
    acc_mock_1.assert_called_once() 
    assert t.is_success()
    assert t.result() == ('cafebabe', '42')


def test_path_payment():
    trx_env = 'AAAAAGxfNmJ5gxclDy95e+IrnQwRrW6LyjVwpoQ2iKOT684jAAAAZABlTtQAAAAZAAAAAAAAAAAAAAABAAAAAQAAAABsXzZieYMXJQ8veXviK50MEa1ui8o1cKaENoijk+vOIwAAAAIAAAACU1JDQVNTRVQAAAAAAAAAAOljdFn2Ets58A72NyrVtJp0gs+zqNAQNZs/CKfeaYuCAAAAADuaygAAAAAA88jvjG1RNbc8VVQSAamm6ZyXOVuv/NadBZHykX0Hk2EAAAACREVTVEFTU0VUAAAAAAAAAOljdFn2Ets58A72NyrVtJp0gs+zqNAQNZs/CKfeaYuCAAAAADuaygAAAAABAAAAAklOVEFTU0VUAAAAAAAAAADpY3RZ9hLbOfAO9jcq1bSadILPs6jQEDWbPwin3mmLggAAAAAAAAABk+vOIwAAAECSgtpCVj4SqV2J29PLLuMxvUm2icED1fX85P0W5A2mr9K2NYS6iCCjM2xAeCtM44UDEKgriObHu399lPTmt6oK'

    with patch.object(stellar.utils.HTTP, 'post', return_value=result) as get_mock:
        with patch.object(stellar.utils.HTTP, 'get', return_value=acc) as acc_mock:
            with stellar.new_transaction('SALCB22A3PL2JFI3GE62BM4S2TE64NJZP4GF2DBGPBC6QIUQ7GI7BRBN') as t:
                t.pathpay('GDZ4R34MNVITLNZ4KVKBEANJU3UZZFZZLOX7ZVU5AWI7FEL5A6JWDM24', 
                        '100', ('DESTASSET', 'GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ'),
                        '100', ('SRCASSET', 'GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ'), 
                        path=[('INTASSET', 'GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ')])

    get_mock.assert_called_once_with('https://horizon-testnet.stellar.org/transactions/', { 'tx' : trx_env })
    acc_mock.assert_called_once() 
    assert t.is_success()
    assert t.result() == ('cafebabe', '42')

def test_add_offer():
    trx_env = 'AAAAAGxfNmJ5gxclDy95e+IrnQwRrW6LyjVwpoQ2iKOT684jAAAAZABlTtQAAAAZAAAAAAAAAAAAAAABAAAAAQAAAABsXzZieYMXJQ8veXviK50MEa1ui8o1cKaENoijk+vOIwAAAAMAAAABU0VMQQAAAADpY3RZ9hLbOfAO9jcq1bSadILPs6jQEDWbPwin3mmLggAAAAFCVVlBAAAAAOljdFn2Ets58A72NyrVtJp0gs+zqNAQNZs/CKfeaYuCAAAAABAX34AAAAALAAAAAQAAAAAAAAAAAAAAAAAAAAGT684jAAAAQA/v8HOdZJ1sUxJCChS9ou7OthwuWssY3OaGlGc6QRFqpEy5Wi8JR8gBZaWbQOWISiMJ9FOB0ouOVkyvC+zsYQc='

    with patch.object(stellar.utils.HTTP, 'post', return_value=result) as get_mock:
        with patch.object(stellar.utils.HTTP, 'get', return_value=acc) as acc_mock:
            with stellar.new_transaction('SALCB22A3PL2JFI3GE62BM4S2TE64NJZP4GF2DBGPBC6QIUQ7GI7BRBN') as t:
                t.add_offer('27', 
                        ('SELA', 'GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ'),
                        ('BUYA', 'GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ'), 
                        price = (11, 1))

    get_mock.assert_called_once_with('https://horizon-testnet.stellar.org/transactions/', { 'tx' : trx_env })
    acc_mock.assert_called_once() 
    assert t.is_success()
    assert t.result() == ('cafebabe', '42')

def test_add_passive_offer():
    trx_env = 'AAAAAGxfNmJ5gxclDy95e+IrnQwRrW6LyjVwpoQ2iKOT684jAAAAZABlTtQAAAAZAAAAAAAAAAAAAAABAAAAAQAAAABsXzZieYMXJQ8veXviK50MEa1ui8o1cKaENoijk+vOIwAAAAQAAAABU0VMQQAAAADpY3RZ9hLbOfAO9jcq1bSadILPs6jQEDWbPwin3mmLggAAAAFCVVlBAAAAAOljdFn2Ets58A72NyrVtJp0gs+zqNAQNZs/CKfeaYuCAAAAABAX34AAAAANAAAAAQAAAAAAAAABk+vOIwAAAEAylp9GTW4OXmYyjEf0ss/kOw6LNTtBE3u/0Gozavb/6m1fvRbK5ZGEzXXazt5jpdMngjpkf1FYkGZM7+9N1U0A'

    with patch.object(stellar.utils.HTTP, 'post', return_value=result) as get_mock:
        with patch.object(stellar.utils.HTTP, 'get', return_value=acc) as acc_mock:
            with stellar.new_transaction('SALCB22A3PL2JFI3GE62BM4S2TE64NJZP4GF2DBGPBC6QIUQ7GI7BRBN') as t:
                t.add_passive_offer('27', 
                        ('SELA', 'GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ'),
                        ('BUYA', 'GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ'), 
                        price = (13, 1))

    get_mock.assert_called_once_with('https://horizon-testnet.stellar.org/transactions/', { 'tx' : trx_env })
    acc_mock.assert_called_once() 
    assert t.is_success()
    assert t.result() == ('cafebabe', '42')


def test_update_offer():
    trx_env = 'AAAAAGxfNmJ5gxclDy95e+IrnQwRrW6LyjVwpoQ2iKOT684jAAAAZABlTtQAAAAZAAAAAAAAAAAAAAABAAAAAQAAAABsXzZieYMXJQ8veXviK50MEa1ui8o1cKaENoijk+vOIwAAAAMAAAABU0VMQQAAAADpY3RZ9hLbOfAO9jcq1bSadILPs6jQEDWbPwin3mmLggAAAAFCVVlBAAAAAOljdFn2Ets58A72NyrVtJp0gs+zqNAQNZs/CKfeaYuCAAAAABAX34AAAAABAAAACwAAAAAAADAhAAAAAAAAAAGT684jAAAAQAG4SANUDdBC2PfDDvKVdrjphJN7trYxUobk2JVM3+8IEFBOx5EL5mA4oXlUXyEi4IzjyIJF9YoO50f56Gg6FgY='

    with patch.object(stellar.utils.HTTP, 'post', return_value=result) as get_mock:
        with patch.object(stellar.utils.HTTP, 'get', return_value=acc) as acc_mock:
            with stellar.new_transaction('SALCB22A3PL2JFI3GE62BM4S2TE64NJZP4GF2DBGPBC6QIUQ7GI7BRBN') as t:
                t.update_offer(12321, '27', ('SELA', 'GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ'),
                        ('BUYA', 'GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ'), 
                        price = (1, 11))

    get_mock.assert_called_once_with('https://horizon-testnet.stellar.org/transactions/', { 'tx' : trx_env })
    acc_mock.assert_called_once() 
    assert t.is_success()
    assert t.result() == ('cafebabe', '42')

def test_remove_offer():
    trx_env = 'AAAAAGxfNmJ5gxclDy95e+IrnQwRrW6LyjVwpoQ2iKOT684jAAAAZABlTtQAAAAZAAAAAAAAAAAAAAABAAAAAQAAAABsXzZieYMXJQ8veXviK50MEa1ui8o1cKaENoijk+vOIwAAAAMAAAABU0VMQQAAAADpY3RZ9hLbOfAO9jcq1bSadILPs6jQEDWbPwin3mmLggAAAAFCVVlBAAAAAOljdFn2Ets58A72NyrVtJp0gs+zqNAQNZs/CKfeaYuCAAAAAAAAAAAAAAABAAAAAQAAAAAAADAhAAAAAAAAAAGT684jAAAAQIMGTo357twG/BdhJZpUFwtfji6vK+4exwUZOdu+zfS4zZfU/U1DyxwUesAx3A53yY6qbLuQ2j5dhWr7PIZHrgo='

    with patch.object(stellar.utils.HTTP, 'post', return_value=result) as get_mock:
        with patch.object(stellar.utils.HTTP, 'get', return_value=acc) as acc_mock:
            with stellar.new_transaction('SALCB22A3PL2JFI3GE62BM4S2TE64NJZP4GF2DBGPBC6QIUQ7GI7BRBN') as t:
                t.remove_offer(12321, ('SELA', 'GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ'),
                        ('BUYA', 'GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ'))

    get_mock.assert_called_once_with('https://horizon-testnet.stellar.org/transactions/', { 'tx' : trx_env })
    acc_mock.assert_called_once() 
    assert t.is_success()
    assert t.result() == ('cafebabe', '42')


def test_set_inflation():
    trx_env = 'AAAAAGxfNmJ5gxclDy95e+IrnQwRrW6LyjVwpoQ2iKOT684jAAAAZABlTtQAAAAZAAAAAAAAAAAAAAABAAAAAQAAAABsXzZieYMXJQ8veXviK50MEa1ui8o1cKaENoijk+vOIwAAAAUAAAABAAAAAOljdFn2Ets58A72NyrVtJp0gs+zqNAQNZs/CKfeaYuCAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAZPrziMAAABA/1oRN7C7T/B4/d0vsRO3ZbFrNwdbPT5Qfy9hIGcbAgAhKXq/U/wB8cMHBi27rMlGOeTgfBO/IlemOmgnsuskBA=='

    with patch.object(stellar.utils.HTTP, 'post', return_value=result) as get_mock:
        with patch.object(stellar.utils.HTTP, 'get', return_value=acc) as acc_mock:
            with stellar.new_transaction('SALCB22A3PL2JFI3GE62BM4S2TE64NJZP4GF2DBGPBC6QIUQ7GI7BRBN') as t:
                t.set_inflation_destination('GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ')

    get_mock.assert_called_once_with('https://horizon-testnet.stellar.org/transactions/', { 'tx' : trx_env })
    acc_mock.assert_called_once() 
    assert t.is_success()
    assert t.result() == ('cafebabe', '42')

def test_set_flags():
    trx_env = 'AAAAAGxfNmJ5gxclDy95e+IrnQwRrW6LyjVwpoQ2iKOT684jAAAAZABlTtQAAAAZAAAAAAAAAAAAAAABAAAAAQAAAABsXzZieYMXJQ8veXviK50MEa1ui8o1cKaENoijk+vOIwAAAAUAAAAAAAAAAAAAAAEAAAAHAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGT684jAAAAQDSviVGWheyuIeB7BMRJGONYx3LbAG974rfDIGPnt81uO/gPN3fM/HrE2XtdGQRW1nVWdycyfP03fgj1X3lAfQE='

    with patch.object(stellar.utils.HTTP, 'post', return_value=result) as get_mock:
        with patch.object(stellar.utils.HTTP, 'get', return_value=acc) as acc_mock:
            with stellar.new_transaction('SALCB22A3PL2JFI3GE62BM4S2TE64NJZP4GF2DBGPBC6QIUQ7GI7BRBN') as t:
                t.set_flags(True, True, True)

    get_mock.assert_called_once_with('https://horizon-testnet.stellar.org/transactions/', { 'tx' : trx_env })
    acc_mock.assert_called_once() 
    assert t.is_success()
    assert t.result() == ('cafebabe', '42')

def test_clear_flags():
    trx_env = 'AAAAAGxfNmJ5gxclDy95e+IrnQwRrW6LyjVwpoQ2iKOT684jAAAAZABlTtQAAAAZAAAAAAAAAAAAAAABAAAAAQAAAABsXzZieYMXJQ8veXviK50MEa1ui8o1cKaENoijk+vOIwAAAAUAAAAAAAAAAQAAAAcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGT684jAAAAQIr3NOb3reClqtoQg6ELYnkPXhJaKtqh14jTQFNr1RoL/nT+OWRF0QoHfcF8CRK6LjqqGY3kiGbPuwQ32ZXicQc='

    with patch.object(stellar.utils.HTTP, 'post', return_value=result) as get_mock:
        with patch.object(stellar.utils.HTTP, 'get', return_value=acc) as acc_mock:
            with stellar.new_transaction('SALCB22A3PL2JFI3GE62BM4S2TE64NJZP4GF2DBGPBC6QIUQ7GI7BRBN') as t:
                t.clear_flags(True, True, True)

    get_mock.assert_called_once_with('https://horizon-testnet.stellar.org/transactions/', { 'tx' : trx_env })
    acc_mock.assert_called_once() 
    assert t.is_success()
    assert t.result() == ('cafebabe', '42')


def test_set_thresholds():
    trx_env = 'AAAAAGxfNmJ5gxclDy95e+IrnQwRrW6LyjVwpoQ2iKOT684jAAAAZABlTtQAAAAZAAAAAAAAAAAAAAABAAAAAQAAAABsXzZieYMXJQ8veXviK50MEa1ui8o1cKaENoijk+vOIwAAAAUAAAAAAAAAAAAAAAAAAAAAAAAAAQAAACkAAAABAAAAKgAAAAEAAAArAAAAAAAAAAAAAAAAAAAAAZPrziMAAABAKTWKJIY4ssAPCg+HrgKnN9t9Qjhkh1qGR7lXkNvKeD5bMNHI3aDhXKE+ue6Q2xZK2AfDH54WyWgTsPBuMZXuDg=='

    with patch.object(stellar.utils.HTTP, 'post', return_value=result) as get_mock:
        with patch.object(stellar.utils.HTTP, 'get', return_value=acc) as acc_mock:
            with stellar.new_transaction('SALCB22A3PL2JFI3GE62BM4S2TE64NJZP4GF2DBGPBC6QIUQ7GI7BRBN') as t:
                t.set_thresholds(43, 42, 41)

    get_mock.assert_called_once_with('https://horizon-testnet.stellar.org/transactions/', { 'tx' : trx_env })
    acc_mock.assert_called_once() 
    assert t.is_success()
    assert t.result() == ('cafebabe', '42')

def test_set_master_weight():
    trx_env = 'AAAAAGxfNmJ5gxclDy95e+IrnQwRrW6LyjVwpoQ2iKOT684jAAAAZABlTtQAAAAZAAAAAAAAAAAAAAABAAAAAQAAAABsXzZieYMXJQ8veXviK50MEa1ui8o1cKaENoijk+vOIwAAAAUAAAAAAAAAAAAAAAAAAAABAAAAKgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGT684jAAAAQP0XzKC5xnLUdLWCYs1epUQAsXiCdKDBittXPF7GxeyrKNWy1vMBt3aXY2n7UkFGtmbrYRo30wom0N8mU5MQTAE='

    with patch.object(stellar.utils.HTTP, 'post', return_value=result) as get_mock:
        with patch.object(stellar.utils.HTTP, 'get', return_value=acc) as acc_mock:
            with stellar.new_transaction('SALCB22A3PL2JFI3GE62BM4S2TE64NJZP4GF2DBGPBC6QIUQ7GI7BRBN') as t:
                t.set_master_weight(42)

    get_mock.assert_called_once_with('https://horizon-testnet.stellar.org/transactions/', { 'tx' : trx_env })
    acc_mock.assert_called_once() 
    assert t.is_success()
    assert t.result() == ('cafebabe', '42')

def test_set_signer():
    trx_env = 'AAAAAGxfNmJ5gxclDy95e+IrnQwRrW6LyjVwpoQ2iKOT684jAAAAZABlTtQAAAAZAAAAAAAAAAAAAAABAAAAAQAAAABsXzZieYMXJQ8veXviK50MEa1ui8o1cKaENoijk+vOIwAAAAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEAAAAA6WN0WfYS2znwDvY3KtW0mnSCz7Oo0BA1mz8Ip95pi4IAAAAqAAAAAAAAAAGT684jAAAAQFTxotmdA5jzK21LYDYVJNNtYgZ0croGBknBcEiATCCURwzeFMCZXIWBq6bXG9maWDSSNxxiMjylZZWDvCqveAY='

    with patch.object(stellar.utils.HTTP, 'post', return_value=result) as get_mock:
        with patch.object(stellar.utils.HTTP, 'get', return_value=acc) as acc_mock:
            with stellar.new_transaction('SALCB22A3PL2JFI3GE62BM4S2TE64NJZP4GF2DBGPBC6QIUQ7GI7BRBN') as t:
                t.set_signer('ed25519PublicKey', 'GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ', 42)

    get_mock.assert_called_once_with('https://horizon-testnet.stellar.org/transactions/', { 'tx' : trx_env })
    acc_mock.assert_called_once() 
    assert t.is_success()
    assert t.result() == ('cafebabe', '42')

def test_set_home_domain():
    trx_env = 'AAAAAGxfNmJ5gxclDy95e+IrnQwRrW6LyjVwpoQ2iKOT684jAAAAZABlTtQAAAAZAAAAAAAAAAAAAAABAAAAAQAAAABsXzZieYMXJQ8veXviK50MEa1ui8o1cKaENoijk+vOIwAAAAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAAABN3d3cuaG9tZS1kb21haW4uY29tAAAAAAAAAAAAAAAAAZPrziMAAABA1Lyg54Rdb5MY1Ur6v0hDVzScn8mZuBRugJwAV9JhcWbp9gxksEHFf1FeMmfZZCNkNaoWPE0Sct9hGpzy2sV3Aw=='

    with patch.object(stellar.utils.HTTP, 'post', return_value=result) as get_mock:
        with patch.object(stellar.utils.HTTP, 'get', return_value=acc) as acc_mock:
            with stellar.new_transaction('SALCB22A3PL2JFI3GE62BM4S2TE64NJZP4GF2DBGPBC6QIUQ7GI7BRBN') as t:
                t.set_home_domain('www.home-domain.com')

    get_mock.assert_called_once_with('https://horizon-testnet.stellar.org/transactions/', { 'tx' : trx_env })
    acc_mock.assert_called_once() 
    assert t.is_success()
    assert t.result() == ('cafebabe', '42')


