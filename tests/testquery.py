import base64
import hashlib
import datetime
import stellar
import stellar.utils
from mock import patch

def test_network_setup():
    stellar.setup_test_network()
    (horizon, network_id) = stellar.get_current_network()
    assert stellar.api.HORIZON_TESTNET_ENDPOINT == horizon
    assert hashlib.sha256(stellar.api.NETWORK_PASSWORD_TESTNET).digest() == network_id

    stellar.setup_public_network()
    (horizon, network_id) = stellar.get_current_network()
    assert stellar.api.HORIZON_PUBLIC_ENDPOINT == horizon
    assert hashlib.sha256(stellar.api.NETWORK_PASSWORD_PUBLIC).digest() == network_id

    custom_network = 'http://horizon.sirius.com'
    custom_network_password = 'Why so sirius'
    stellar.setup_custom_network(custom_network, custom_network_password)
    (horizon, network_id) = stellar.get_current_network()
    assert custom_network == horizon
    assert hashlib.sha256(custom_network_password).digest() == network_id

def test_shorten_address():
    address = 'GDZ4R34MNVITLNZ4KVKBEANJU3UZZFZZLOX7ZVU5AWI7FEL5A6JWDM24'
    shortened_address = stellar.api.shorten_address(address)
    assert len(shortened_address) == 10 and shortened_address.startswith(address[:4]) and\
            shortened_address.endswith(address[-4:])

def test_account_fetch():
    stellar.setup_test_network()
    acc =   { 
            "id" : "GDZ4R34MNVITLNZ4KVKBEANJU3UZZFZZLOX7ZVU5AWI7FEL5A6JWDM24",
            "paging_token": "",
            "account_id": "GDZ4R34MNVITLNZ4KVKBEANJU3UZZFZZLOX7ZVU5AWI7FEL5A6JWDM24",
            "sequence": "28551671273488385",
            "subentry_count": 5,
            "inflation_destination": "GCCD6AJOYZCUAQLX32ZJF2MKFFAUJ53PVCFQI3RHWKL3V47QYE2BNAUT",
            "thresholds": {
                "low_threshold": 1,
                "med_threshold": 2,
                "high_threshold": 3
                },
            "flags": {
                "auth_required": True,
                "auth_revocable": False
                },
            "balances": [
                {
                    "balance": "42.0000001",
                    "limit": "1000.0000000",
                    "asset_type": "credit_alphanum4",
                    "asset_code": "USD",
                    "asset_issuer": "GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ"
                    },
                {
                    "balance": "42.0000002",
                    "limit": "2000.0000000",
                    "asset_type": "credit_alphanum12",
                    "asset_code": "COOLUSD",
                    "asset_issuer": "GDUTILHAQK6R2THKLKDQGIABZXFFS6XMY2ZL6DRU3LKZ4ULUSI3ALB7X"
                    },

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
                {
                    "public_key": "TABGNX36UIFE5JCVFIFUAT2FIHU7TKF2LRJKOARTPFWWNFRYM5MHH5B3",
                    "weight": 43,
                    "key": "TABGNX36UIFE5JCVFIFUAT2FIHU7TKF2LRJKOARTPFWWNFRYM5MHH5B3",
                    "type": "preauth_tx"
                    },
                {
                    "public_key": "XABGNX36UIFE5JCVFIFUAT2FIHU7TKF2LRJKOARTPFWWNFRYM5MHGZEC",
                    "weight": 44,
                    "key": "XABGNX36UIFE5JCVFIFUAT2FIHU7TKF2LRJKOARTPFWWNFRYM5MHGZEC",
                    "type": "sha256_hash"
                    },
                ],
            "data": {
                    "image_link": "aHR0cDovL2JpdC5seS8yRkFKc0ow"
                    }
            }
    accid = 'GDZ4R34MNVITLNZ4KVKBEANJU3UZZFZZLOX7ZVU5AWI7FEL5A6JWDM24'
    horizon, _ = stellar.get_current_network()
    endpoint = horizon + '/accounts/GDZ4R34MNVITLNZ4KVKBEANJU3UZZFZZLOX7ZVU5AWI7FEL5A6JWDM24'
    with patch.object(stellar.utils.HTTP, 'get', return_value=acc) as get_mock:
        a = stellar.account(accid).fetch()

        get_mock.assert_called_once_with(endpoint)
        assert a.account_id == accid
        assert a.sequence == '28551671273488385'
        assert len(a.data) == 1 and a.data[0].key == 'image_link'\
                and a.data[0].value == 'http://bit.ly/2FAJsJ0'

        assert len(a.signers) == 3
        found = 0
        for s in a.signers:
            if s.type == 'ed25519_public_key':
                assert s.public_key == 'GDZ4R34MNVITLNZ4KVKBEANJU3UZZFZZLOX7ZVU5AWI7FEL5A6JWDM24'
                assert s.weight == 42
                assert s.key == 'GDZ4R34MNVITLNZ4KVKBEANJU3UZZFZZLOX7ZVU5AWI7FEL5A6JWDM24'
                found += 1
            elif s.type == 'preauth_tx':
                assert s.public_key == 'TABGNX36UIFE5JCVFIFUAT2FIHU7TKF2LRJKOARTPFWWNFRYM5MHH5B3'
                assert s.weight == 43
                assert s.key == 'TABGNX36UIFE5JCVFIFUAT2FIHU7TKF2LRJKOARTPFWWNFRYM5MHH5B3'
                found += 1
            elif s.type == 'sha256_hash':
                assert s.public_key == 'XABGNX36UIFE5JCVFIFUAT2FIHU7TKF2LRJKOARTPFWWNFRYM5MHGZEC'
                assert s.weight == 44
                assert s.key == 'XABGNX36UIFE5JCVFIFUAT2FIHU7TKF2LRJKOARTPFWWNFRYM5MHGZEC'
                found += 1
        assert found == 3

        assert len(a.balances) == 3
        found = 0
        for b in a.balances:
            if b.asset.asset_code == 'XLM':
                assert b.asset.asset_type == 'native'
                assert b.balance == '9999.9999900'
                found += 1
            elif b.asset.asset_code == 'USD':
                assert b.asset.asset_type == 'credit_alphanum4'
                assert b.asset.asset_issuer == 'GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ'
                assert b.balance == '42.0000001'
                found += 1
            elif b.asset.asset_code == 'COOLUSD':
                assert b.asset.asset_type == 'credit_alphanum12'
                assert b.asset.asset_issuer == 'GDUTILHAQK6R2THKLKDQGIABZXFFS6XMY2ZL6DRU3LKZ4ULUSI3ALB7X'
                assert b.balance == '42.0000002'
                found += 1
        assert found == 3

        assert a.flags.auth_required == True
        assert a.flags.auth_revocable == False
        assert a.thresholds.low_threshold == 1
        assert a.thresholds.med_threshold == 2
        assert a.thresholds.high_threshold == 3
        assert a.subentry_count == 5
        assert a.inflation_destination == 'GCCD6AJOYZCUAQLX32ZJF2MKFFAUJ53PVCFQI3RHWKL3V47QYE2BNAUT'

def test_transaction_fetch():
    stellar.setup_test_network()
    trx = {
            "id": "d3c75596c719f3c4af977d29db5ba0e21b0c487ba62b6902b7a222b7dc6b7dc1",
            "paging_token": "64034663848484864",
            "hash": "d3c75596c719f3c4af977d29db5ba0e21b0c487ba62b6902b7a222b7dc6b7dc1",
            "ledger": 14909232,
            "created_at": "2017-12-05T10:43:13Z",
            "source_account": "GACJFMOXTSE7QOL5HNYI2NIAQ4RDHZTGD6FNYK4P5THDVNWIKQDGOODU",
            "source_account_sequence": "48388037859606661",
            "fee_paid": 200,
            "operation_count": 1,
            "envelope_xdr": "AAAAAASSsdecifg5fTtwjTUAhyIz5mYfitwrj+zOOrbIVAZnAAAAZACr6KoAAACFAAAAAAAAAAEAAAAQSGF2ZSBhIG5pY2UgZGF5IQAAAAEAAAAAAAAAAAAAAACdpD9sS2jlS4+g0cF9ZjMgNJrm2J2L7tIPDnaA6sV7hQAAAAA7msoAAAAAAAAAAAHIVAZnAAAAQEb1W4VjSLuV0OviLu8XxizSUN+jsnuVq0SSTmJWcA5o9OSVRtWat6LVMKJAAW6BaWjyT6QGwnJC1SA5dz3oGw0=",
            "result_xdr": "AAAAAAAAAGQAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAA=",
            "result_meta_xdr": "AAAAAAAAAAEAAAADAAAAAADjfzAAAAAAAAAAAJ2kP2xLaOVLj6DRwX1mMyA0mubYnYvu0g8OdoDqxXuFAAAAADuaygAA438wAAAAAAAAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAwDjfzAAAAAAAAAAAASSsdecifg5fTtwjTUAhyIz5mYfitwrj+zOOrbIVAZnAAAAFJDzwekAq+iqAAAAhQAAAAoAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAQDjfzAAAAAAAAAAAASSsdecifg5fTtwjTUAhyIz5mYfitwrj+zOOrbIVAZnAAAAFFVY9+kAq+iqAAAAhQAAAAoAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAA",
            "fee_meta_xdr": "AAAAAgAAAAMA4mDqAAAAAAAAAAAEkrHXnIn4OX07cI01AIciM+ZmH4rcK4/szjq2yFQGZwAAABSQ88JNAKvoqgAAAIQAAAAKAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAEA438wAAAAAAAAAAAEkrHXnIn4OX07cI01AIciM+ZmH4rcK4/szjq2yFQGZwAAABSQ88HpAKvoqgAAAIUAAAAKAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAA==",
            "memo_type": "text",
            "memo": "Have a nice day!",
            "signatures": [
                "RvVbhWNIu5XQ6+Iu7xfGLNJQ36Oye5WrRJJOYlZwDmj05JVG1Zq3otUwokABboFpaPJPpAbCckLVIDl3PegbDQ=="
                ]
            }

    trxid = 'd3c75596c719f3c4af977d29db5ba0e21b0c487ba62b6902b7a222b7dc6b7dc1'
    horizon, _ = stellar.get_current_network()
    endpoint = horizon + '/transactions/d3c75596c719f3c4af977d29db5ba0e21b0c487ba62b6902b7a222b7dc6b7dc1'
    with patch.object(stellar.utils.HTTP, 'get', return_value=trx) as get_mock:
        t = stellar.transaction(trxid).fetch()

        get_mock.assert_called_once_with(endpoint)
        assert t.trxid == trxid
        assert t.paging_token == '64034663848484864'
        assert t.hash == trxid
        assert t.ledger == 14909232
        assert t.account == 'GACJFMOXTSE7QOL5HNYI2NIAQ4RDHZTGD6FNYK4P5THDVNWIKQDGOODU'
        assert t.account_seq == '48388037859606661'
        assert t.fee_paid == 200
        assert t.operation_count == 1
        assert t.memo == ('text', 'Have a nice day!')
        assert t.created_at == datetime.datetime.strptime('2017-12-05T10:43:13Z', '%Y-%m-%dT%H:%M:%SZ')

def test_transactions_fetch():
    stellar.setup_test_network()
    trxs = {
            "_links": {
                "self": {
                    "href": "https://horizon.stellar.org/transactions?order=desc&limit=2&cursor=64034663848484864"
                    },
                "next": {
                    "href": "https://horizon.stellar.org/transactions?order=desc&limit=2&cursor=64034646668611584"
                    },
                "prev": {
                    "href": "https://horizon.stellar.org/transactions?order=asc&limit=2&cursor=64034659553513472"
                    }
                },
            "_embedded": {
                "records": [
                    {
                        "id": "4986e01e14f60050c99038153362a1a9d72408a67b3da7d9642f9ae3f0255e5b",
                        "paging_token": "64034659553513472",
                        "hash": "4986e01e14f60050c99038153362a1a9d72408a67b3da7d9642f9ae3f0255e5b",
                        "ledger": 14909231,
                        "created_at": "2017-12-05T10:43:05Z",
                        "source_account": "GCGNWKCJ3KHRLPM3TM6N7D3W5YKDJFL6A2YCXFXNMRTZ4Q66MEMZ6FI2",
                        "source_account_sequence": "2530306968038009",
                        "fee_paid": 100,
                        "operation_count": 1,
                        "envelope_xdr": "AAAAAIzbKEnajxW9m5s834927hQ0lX4GsCuW7WRnnkPeYRmfAAAAZAAI/U0AAKp5AAAAAAAAAAIAAAAAAAAAAQAAAAEAAAAAAAAAAQAAAAAZuDCOD4qqI/b1MUetNFnfLBZhiesUnvykkhirJ/T3bgAAAAAAAAAMVwvSAAAAAAAAAAAB3mEZnwAAAEA9NyKl2Tx6ibw2j1Df84XFuX35Fiye9LLiwcehtcsnI/x/rDt2HYsZnQJ8vBOH/0tfNxDDozaj73CrzkUxceQH",
                        "result_xdr": "AAAAAAAAAGQAAAAAAAAAAQAAAAAAAAABAAAAAAAAAAA=",
                        "result_meta_xdr": "AAAAAAAAAAEAAAAEAAAAAwDjfrIAAAAAAAAAABm4MI4Piqoj9vUxR600Wd8sFmGJ6xSe/KSSGKsn9PduAAABEkPjKZwA4oZqAAAAAQAAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAQDjfy8AAAAAAAAAABm4MI4Piqoj9vUxR600Wd8sFmGJ6xSe/KSSGKsn9PduAAABHpru+5wA4oZqAAAAAQAAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAwDjfy8AAAAAAAAAAIzbKEnajxW9m5s834927hQ0lX4GsCuW7WRnnkPeYRmfABsLtIG/73UACP1NAACqeQAAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAQDjfy8AAAAAAAAAAIzbKEnajxW9m5s834927hQ0lX4GsCuW7WRnnkPeYRmfABsLqCq0HXUACP1NAACqeQAAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAA",
                        "fee_meta_xdr": "AAAAAgAAAAMA437xAAAAAAAAAACM2yhJ2o8VvZubPN+Pdu4UNJV+BrArlu1kZ55D3mEZnwAbC7SBv+/ZAAj9TQAAqngAAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAEA438vAAAAAAAAAACM2yhJ2o8VvZubPN+Pdu4UNJV+BrArlu1kZ55D3mEZnwAbC7SBv+91AAj9TQAAqnkAAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAA==",
                        "memo_type": "id",
                        "memo": "1",
                        "signatures": [
                            "PTcipdk8eom8No9Q3/OFxbl9+RYsnvSy4sHHobXLJyP8f6w7dh2LGZ0CfLwTh/9LXzcQw6M2o+9wq85FMXHkBw=="
                            ]
                        },
                    {
                        "id": "7b4bfb411e2a188223dd7dae521d46e661cd9b3b1fc19f926a69d3e68f35ff48",
                        "paging_token": "64034646668611584",
                        "hash": "7b4bfb411e2a188223dd7dae521d46e661cd9b3b1fc19f926a69d3e68f35ff48",
                        "ledger": 14909228,
                        "created_at": "2017-12-05T10:42:53Z",
                        "source_account": "GAJFOPLTY5LSQHDEY4ETFCSK6B5CWWSUSVKQSSAHQXGMXQTYQPZRBR5R",
                        "source_account_sequence": "64017660072952069",
                        "fee_paid": 200,
                        "operation_count": 2,
                        "envelope_xdr": "AAAAABJXPXPHVygcZMcJMopK8HorWlSVVQlIB4XMy8J4g/MQAAAAyADjb7kAAAEFAAAAAAAAAAAAAAACAAAAAQAAAABaSx+NQbFWAINd6rBR6+Ysqe86VFfDq56LYSyxpI7pnQAAAAEAAAAAQnlYW7yoVRCjfB2+eCJbNkAk6BWjWVUQcbmAoPsGqiQAAAAAAAAAAAX14QAAAAABAAAAAEJ5WFu8qFUQo3wdvngiWzZAJOgVo1lVEHG5gKD7BqokAAAAAwAAAAFFVEgAAAAAAGU4n5B07NlUHicOUkSTvzK5R2JFArV8F8IRr/3lSLgQAAAAAVhMTQAAAAAAZTifkHTs2VQeJw5SRJO/MrlHYkUCtXwXwhGv/eVIuBAAAAAAAAGVFHGwfBoABglJAAAAAAAAAAAAAAAAAAAAA6SO6Z0AAABA3vxKes0ZraLyPGVWE71J01GSSqXqBwQvc/M6S+hd2URfLtIsMsagd1tn5netIUxHPqaqyDV3qQoimP1EYpXSBvsGqiQAAABAJ/mA0RdCuLypvDA+mgw18rku9Srx4n+X9I30XXBCjYNRfZqD0ymCIdUNmEEq+InvAzlxts/a4pUAyCfKUyBoB1EiycMAAABAVLHvzrDD7YuafaeH8FveRQxpheJyLNaTlmMaJBTH1iEAw/OM9EMqOXskn9bo5uqSUs831ZLV0WZHjiWm2A7ADA==",
                        "result_xdr": "AAAAAAAAAMgAAAAAAAAAAgAAAAAAAAABAAAAAAAAAAAAAAADAAAAAAAAAAAAAAAAAAAAAEJ5WFu8qFUQo3wdvngiWzZAJOgVo1lVEHG5gKD7BqokAAAAAAAD7VcAAAABRVRIAAAAAABlOJ+QdOzZVB4nDlJEk78yuUdiRQK1fBfCEa/95Ui4EAAAAAFYTE0AAAAAAGU4n5B07NlUHicOUkSTvzK5R2JFArV8F8IRr/3lSLgQAAAAAAABlRRxsHwaAAYJSQAAAAAAAAAAAAAAAA==",
                        "result_meta_xdr": "AAAAAAAAAAIAAAAEAAAAAwDjfysAAAAAAAAAAEJ5WFu8qFUQo3wdvngiWzZAJOgVo1lVEHG5gKD7BqokAAAAADWk6QAA3S1GAAAATgAAAAcAAAABAAAAABDSrxNZ7yepCLlo726b4XmZuiam/peAV50jyAmHcUVVAAAAAAAAAA1zdHJvbmdob2xkLmNvAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAEA438sAAAAAAAAAABCeVhbvKhVEKN8Hb54Ils2QCToFaNZVRBxuYCg+waqJAAAAAA7msoAAN0tRgAAAE4AAAAHAAAAAQAAAAAQ0q8TWe8nqQi5aO9um+F5mbompv6XgFedI8gJh3FFVQAAAAAAAAANc3Ryb25naG9sZC5jbwAAAAEAAAAAAAAAAAAAAAAAAAAAAAADAON/KwAAAAAAAAAAWksfjUGxVgCDXeqwUevmLKnvOlRXw6uei2EssaSO6Z0AAAfr9yLiawDSkAcAAAAAAAAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAAAABAON/LAAAAAAAAAAAWksfjUGxVgCDXeqwUevmLKnvOlRXw6uei2EssaSO6Z0AAAfr8S0BawDSkAcAAAAAAAAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAAAADAAAAAADjfywAAAACAAAAAEJ5WFu8qFUQo3wdvngiWzZAJOgVo1lVEHG5gKD7BqokAAAAAAAD7VcAAAABRVRIAAAAAABlOJ+QdOzZVB4nDlJEk78yuUdiRQK1fBfCEa/95Ui4EAAAAAFYTE0AAAAAAGU4n5B07NlUHicOUkSTvzK5R2JFArV8F8IRr/3lSLgQAAAAAAABlRRxsHwaAAYJSQAAAAAAAAAAAAAAAAAAAAMA438sAAAAAAAAAABCeVhbvKhVEKN8Hb54Ils2QCToFaNZVRBxuYCg+waqJAAAAAA7msoAAN0tRgAAAE4AAAAHAAAAAQAAAAAQ0q8TWe8nqQi5aO9um+F5mbompv6XgFedI8gJh3FFVQAAAAAAAAANc3Ryb25naG9sZC5jbwAAAAEAAAAAAAAAAAAAAAAAAAAAAAABAON/LAAAAAAAAAAAQnlYW7yoVRCjfB2+eCJbNkAk6BWjWVUQcbmAoPsGqiQAAAAAO5rKAADdLUYAAABOAAAACAAAAAEAAAAAENKvE1nvJ6kIuWjvbpvheZm6Jqb+l4BXnSPICYdxRVUAAAAAAAAADXN0cm9uZ2hvbGQuY28AAAABAAAAAAAAAAAAAAAAAAAA",
                        "fee_meta_xdr": "AAAAAgAAAAMA438iAAAAAAAAAAASVz1zx1coHGTHCTKKSvB6K1pUlVUJSAeFzMvCeIPzEAAAAAASeW5gAONvuQAAAQQAAAABAAAAAAAAAAAAAAAAAQAAAAAAAAEAAAAACkJLjBk7n8PJCHQcMXL+LEPN7Y/QIDcg/MDlslEiycMAAAABAAAAAAAAAAAAAAABAON/LAAAAAAAAAAAElc9c8dXKBxkxwkyikrweitaVJVVCUgHhczLwniD8xAAAAAAEnltmADjb7kAAAEFAAAAAQAAAAAAAAAAAAAAAAEAAAAAAAABAAAAAApCS4wZO5/DyQh0HDFy/ixDze2P0CA3IPzA5bJRIsnDAAAAAQAAAAAAAAAA",
                        "memo_type": "none",
                        "signatures": [
                            "3vxKes0ZraLyPGVWE71J01GSSqXqBwQvc/M6S+hd2URfLtIsMsagd1tn5netIUxHPqaqyDV3qQoimP1EYpXSBg==",
                            "J/mA0RdCuLypvDA+mgw18rku9Srx4n+X9I30XXBCjYNRfZqD0ymCIdUNmEEq+InvAzlxts/a4pUAyCfKUyBoBw==",
                            "VLHvzrDD7YuafaeH8FveRQxpheJyLNaTlmMaJBTH1iEAw/OM9EMqOXskn9bo5uqSUs831ZLV0WZHjiWm2A7ADA=="
                            ]
                        }
                    ]
                }
            }
    
    horizon, _ = stellar.get_current_network()
    endpoint = horizon + '/transactions?cursor=64034663848484864&limit=2&order=desc'
    with patch.object(stellar.utils.HTTP, 'get', return_value=trxs) as get_mock:
        p = stellar.transactions().fetch(cursor='64034663848484864', limit=2, order='desc')

        get_mock.assert_called_once_with(endpoint)
        assert len(p.entries()) == 2
        assert p.entries()[0].trxid == '4986e01e14f60050c99038153362a1a9d72408a67b3da7d9642f9ae3f0255e5b'
        assert p.entries()[1].trxid == '7b4bfb411e2a188223dd7dae521d46e661cd9b3b1fc19f926a69d3e68f35ff48'

def test_ledger_fetch():
    stellar.setup_test_network()
    ledg = {
            "id": "166892c79f8ca9467b171cef05755e31653cf8506321944ae105af82b5c9ec65",
            "paging_token": "64034659553509376",
            "hash": "166892c79f8ca9467b171cef05755e31653cf8506321944ae105af82b5c9ec65",
            "prev_hash": "d137d7a059ebd789814c8a2bdee62fee39268d77a0eab5bbab0744681e1e1bed",
            "sequence": 14909231,
            "transaction_count": 1,
            "operation_count": 1,
            "closed_at": "2017-12-05T10:43:05Z",
            "total_coins": "103491574319.4671445",
            "fee_pool": "1468208.3174628",
            "base_fee": 100,
            "base_reserve": "10.0000000",
            "max_tx_set_size": 50,
            "protocol_version": 8,
            "header_xdr": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            }
    
    ledid = 14909231
    horizon, _ = stellar.get_current_network()
    endpoint = horizon + '/ledgers/14909231'
    with patch.object(stellar.utils.HTTP, 'get', return_value=ledg) as get_mock:
        l = stellar.ledger(ledid).fetch()

        get_mock.assert_called_once_with(endpoint)
        assert l.ledseq == ledid
        assert l.ledid == '166892c79f8ca9467b171cef05755e31653cf8506321944ae105af82b5c9ec65'
        assert l.paging_token == '64034659553509376'
        assert l.hash == '166892c79f8ca9467b171cef05755e31653cf8506321944ae105af82b5c9ec65'
        assert l.prev_hash == 'd137d7a059ebd789814c8a2bdee62fee39268d77a0eab5bbab0744681e1e1bed'
        assert l.transaction_count == 1
        assert l.operation_count == 1
        assert l.total_coins == '103491574319.4671445'
        assert l.fee_pool == '1468208.3174628'
        assert l.base_fee == 100
        assert l.base_reserve == '10.0000000'
        assert l.max_tx_set_size == 50
        assert l.closed_at == datetime.datetime.strptime('2017-12-05T10:43:05Z', '%Y-%m-%dT%H:%M:%SZ')

def test_ledgers_fetch():
    stellar.setup_test_network()
    ledgs = {
            "_links": {
                "self": {
                    "href": "https://horizon.stellar.org/transactions?order=desc&limit=2&cursor=64034663848484864"
                    },
                "next": {
                    "href": "https://horizon.stellar.org/transactions?order=desc&limit=2&cursor=64034646668611584"
                    },
                "prev": {
                    "href": "https://horizon.stellar.org/transactions?order=asc&limit=2&cursor=64034659553513472"
                    }
                },
            "_embedded": {
                "records": [
                    {
                        "id": "d137d7a059ebd789814c8a2bdee62fee39268d77a0eab5bbab0744681e1e1bed",
                        "paging_token": "64034655258542080",
                        "hash": "d137d7a059ebd789814c8a2bdee62fee39268d77a0eab5bbab0744681e1e1bed",
                        "prev_hash": "1c7743b7db949171398b44ba8e50a8a3c07858d6a2c48381c452b917b93b8a0c",
                        "sequence": 14909230,
                        "transaction_count": 0,
                        "operation_count": 0,
                        "closed_at": "2017-12-05T10:43:03Z",
                        "total_coins": "103491574319.4671445",
                        "fee_pool": "1468208.3174528",
                        "base_fee": 100,
                        "base_reserve": "10.0000000",
                        "max_tx_set_size": 50,
                        "protocol_version": 8,
                        "header_xdr": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
                        },
                    {
                        "id": "1c7743b7db949171398b44ba8e50a8a3c07858d6a2c48381c452b917b93b8a0c",
                        "paging_token": "64034650963574784",
                        "hash": "1c7743b7db949171398b44ba8e50a8a3c07858d6a2c48381c452b917b93b8a0c",
                        "prev_hash": "4e5474899a9d6bc9829f6c44df76ec388115cdfee72f79a4144fd9cab62b8202",
                        "sequence": 14909229,
                        "transaction_count": 0,
                        "operation_count": 0,
                        "closed_at": "2017-12-05T10:42:57Z",
                        "total_coins": "103491574319.4671445",
                        "fee_pool": "1468208.3174328",
                        "base_fee": 100,
                        "base_reserve": "10.0000000",
                        "max_tx_set_size": 50,
                        "protocol_version": 8,
                        "header_xdr": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
                        }
                    ]
                }
            }

    horizon, _ = stellar.get_current_network()
    endpoint = horizon + '/ledgers?cursor=64034659553509376&limit=2&order=desc'
    with patch.object(stellar.utils.HTTP, 'get', return_value=ledgs) as get_mock:
        p = stellar.ledgers().fetch(cursor='64034659553509376', limit=2, order='desc')

        get_mock.assert_called_once_with(endpoint)
        assert len(p.entries()) == 2
        assert p.entries()[0].ledseq == 14909230
        assert p.entries()[1].ledseq == 14909229

def test_operation_fetch():
    stellar.setup_test_network()
    oper = {
            "id": "28515937145589761",
            "paging_token": "28515937145589761",
            "source_account": "GBS43BF24ENNS3KPACUZVKK2VYPOZVBQO2CISGZ777RYGOPYC2FT6S3K",
            "type": "create_account",
            "type_i": 0,
            "created_at": "2018-01-13T06:28:58Z",
            "transaction_hash": "aaebfd958a3920d09046f472860e344dc2fcf4e459816126ce7cbc5115c734d6",
            "starting_balance": "10000.0000000",
            "funder": "GBS43BF24ENNS3KPACUZVKK2VYPOZVBQO2CISGZ777RYGOPYC2FT6S3K",
            "account": "GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ"
            }
    
    operid = '28515937145589761'
    horizon, _ = stellar.get_current_network()
    endpoint = horizon + '/operations/28515937145589761'
    with patch.object(stellar.utils.HTTP, 'get', return_value=oper) as get_mock:
        o = stellar.operation(operid).fetch()

        get_mock.assert_called_once_with(endpoint)
        assert o.opid == operid
        assert o.paging_token == operid
        assert o.source_account == 'GBS43BF24ENNS3KPACUZVKK2VYPOZVBQO2CISGZ777RYGOPYC2FT6S3K'
        assert o.type == 'create_account'
        assert o.type_i == 0
        assert o.created_at == datetime.datetime.strptime('2018-01-13T06:28:58Z', '%Y-%m-%dT%H:%M:%SZ')
        assert o.transaction_hash == 'aaebfd958a3920d09046f472860e344dc2fcf4e459816126ce7cbc5115c734d6'


def test_operations_fetch():
    stellar.setup_test_network()
    opers = {
            "_links": {
                "self": {
                    "href": "https://horizon-testnet.stellar.org/accounts/GDUTILHAQK6R2THKLKDQGIABZXFFS6XMY2ZL6DRU3LKZ4ULUSI3ALB7X/operations?cursor=&limit=10&order=asc"
                    },
                "next": {
                    "href": "https://horizon-testnet.stellar.org/accounts/GDUTILHAQK6R2THKLKDQGIABZXFFS6XMY2ZL6DRU3LKZ4ULUSI3ALB7X/operations?cursor=28551112927744001&limit=10&order=asc"
                    },
                "prev": {
                    "href": "https://horizon-testnet.stellar.org/accounts/GDUTILHAQK6R2THKLKDQGIABZXFFS6XMY2ZL6DRU3LKZ4ULUSI3ALB7X/operations?cursor=28515718102257665&limit=10&order=desc"
                    }
                },
            "_embedded": {
                "records": [
                    {
                        "id": "28515718102257665",
                        "paging_token": "28515718102257665",
                        "source_account": "GBS43BF24ENNS3KPACUZVKK2VYPOZVBQO2CISGZ777RYGOPYC2FT6S3K",
                        "type": "create_account",
                        "type_i": 0,
                        "created_at": "2018-01-13T06:24:40Z",
                        "transaction_hash": "2b1596e9b5a332939a8254ff028dd6137437bf41fbfd8470b3af5cc32afbfbf1",
                        "starting_balance": "10000.0000000",
                        "funder": "GBS43BF24ENNS3KPACUZVKK2VYPOZVBQO2CISGZ777RYGOPYC2FT6S3K",
                        "account": "GDUTILHAQK6R2THKLKDQGIABZXFFS6XMY2ZL6DRU3LKZ4ULUSI3ALB7X"
                        },
                    {
                        "id": "28518724579364865",
                        "paging_token": "28518724579364865",
                        "source_account": "GDUTILHAQK6R2THKLKDQGIABZXFFS6XMY2ZL6DRU3LKZ4ULUSI3ALB7X",
                        "type": "change_trust",
                        "type_i": 6,
                        "created_at": "2018-01-13T07:16:15Z",
                        "transaction_hash": "e33a437320fa8e47eea32620d99f3f16da76ce1da8fb01f2eeba93c08432a1b2",
                        "asset_type": "credit_alphanum4",
                        "asset_code": "CODR",
                        "asset_issuer": "GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ",
                        "limit": "922337203685.4775807",
                        "trustee": "GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ",
                        "trustor": "GDUTILHAQK6R2THKLKDQGIABZXFFS6XMY2ZL6DRU3LKZ4ULUSI3ALB7X"
                        },
                    {
                        "id": "28518724579364866",
                        "paging_token": "28518724579364866",
                        "source_account": "GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ",
                        "type": "payment",
                        "type_i": 1,
                        "created_at": "2018-01-13T07:16:15Z",
                        "transaction_hash": "e33a437320fa8e47eea32620d99f3f16da76ce1da8fb01f2eeba93c08432a1b2",
                        "asset_type": "credit_alphanum4",
                        "asset_code": "CODR",
                        "asset_issuer": "GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ",
                        "from": "GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ",
                        "to": "GDUTILHAQK6R2THKLKDQGIABZXFFS6XMY2ZL6DRU3LKZ4ULUSI3ALB7X",
                        "amount": "10000.0040002"
                        },
                    {
                        "id": "31278893902073858",
                        "paging_token": "31278893902073858",
                        "source_account": "GBH25RYXAEDKPZUIMC5VJBKNYRUULY5B2LH5NVG6Q3RZPHK5KPFBZX7T",
                        "type": "manage_offer",
                        "type_i": 3,
                        "created_at": "2018-02-11T13:21:06Z",
                        "transaction_hash": "50ee5f76232ce2792c0c566d7b18b265f6d0e77037ce157cebaa8d6381da2142",
                        "amount": "501.3023222",
                        "price": "0.0183400",
                        "price_r": {
                            "n": 917,
                            "d": 50000
                            },
                        "buying_asset_type": "credit_alphanum4",
                        "buying_asset_code": "BTC",
                        "buying_asset_issuer": "GA77B6GK5K3FH2YJ6I5VJ7VPFZKPBQUX2IIC2MJYAERQTGJI4VOPKRYJ",
                        "selling_asset_type": "credit_alphanum4",
                        "selling_asset_code": "LTC",
                        "selling_asset_issuer": "GA77B6GK5K3FH2YJ6I5VJ7VPFZKPBQUX2IIC2MJYAERQTGJI4VOPKRYJ",
                        "offer_id": 90987
                        },
                    {
                            "id": "31299243457122305",
                            "paging_token": "31299243457122305",
                            "source_account": "GDKGNWAE7N2KH6MLY5GGZUZWK775TH2M7YFIYEYRXDEGZ2OEATD3QKB4",
                            "type": "create_passive_offer",
                            "type_i": 4,
                            "created_at": "2018-02-11T18:22:04Z",
                            "transaction_hash": "450010da60d5ff3f7024eac3486e243240a0b1e954df03eab260dc20e3177085",
                            "amount": "1.0000000",
                            "price": "0.0100000",
                            "price_r": {
                                "n": 1,
                                "d": 100
                                },
                            "buying_asset_type": "credit_alphanum4",
                            "buying_asset_code": "CODR",
                            "buying_asset_issuer": "GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ",
                            "selling_asset_type": "native"
                            },
                    {
                            "id": "28554299793481729",
                            "paging_token": "28554299793481729",
                            "source_account": "GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ",
                            "type": "allow_trust",
                            "type_i": 7,
                            "created_at": "2018-01-13T16:06:34Z",
                            "transaction_hash": "4c365f3888c36d7c882c3f900561e00912dfc39b4586b2211c42dacd503f8958",
                            "asset_type": "credit_alphanum4",
                            "asset_code": "CODR",
                            "asset_issuer": "GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ",
                            "trustee": "GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ",
                            "trustor": "GDKGNWAE7N2KH6MLY5GGZUZWK775TH2M7YFIYEYRXDEGZ2OEATD3QKB4",
                            "authorize": True
                            },
                    {
                            "id": "31296533332758529",
                            "paging_token": "31296533332758529",
                            "source_account": "GBMLESUJT3DMWVQO3SCK3XE2IYETTUO425LF3MEZ6DXG2LBLKCUF5YN7",
                            "type": "set_options",
                            "type_i": 5,
                            "created_at": "2018-02-11T17:41:01Z",
                            "transaction_hash": "a56b24fbc751764a0290614e974305bac6dc0336d3d814deec9cc718fc60f349",
                            "set_flags": [
                                1,
                                2
                                ],
                            "set_flags_s": [
                                "auth_required",
                                "auth_revocable"
                                ]
                            },
                    {
                            "id": "31252247924969473",
                            "paging_token": "31252247924969473",
                            "source_account": "GDLKVPXY663VZIQ2Y2HJCTJ2TLC7UCCBOUTCYI4UPJZS7I4PBWY74FO7",
                            "type": "set_options",
                            "type_i": 5,
                            "created_at": "2018-02-11T06:32:37Z",
                            "transaction_hash": "6eb28ae76a4cd1339ca83c0791bb02476d6f0def9ea90d25330e69b3f307454f",
                            "master_key_weight": 1
                            },
                    {
                            "id": "31296125310869505",
                            "paging_token": "31296125310869505",
                            "source_account": "GCOPFON2ZXRI4EI3QCXK6CJ3TQTQCKP76I7RHGD7F5ETF7SLBHXRQCYZ",
                            "type": "account_merge",
                            "type_i": 8,
                            "created_at": "2018-02-11T17:35:11Z",
                            "transaction_hash": "a54c202925b87eaa4da574cf6bef5e635ca9de98e012f51cdb1b9b2e39d7cebc",
                            "account": "GCOPFON2ZXRI4EI3QCXK6CJ3TQTQCKP76I7RHGD7F5ETF7SLBHXRQCYZ",
                            "into": "GBS43BF24ENNS3KPACUZVKK2VYPOZVBQO2CISGZ777RYGOPYC2FT6S3K"
                            },
                    {
                            "id": "31298813960392705",
                            "paging_token": "31298813960392705",
                            "source_account": "GDKGNWAE7N2KH6MLY5GGZUZWK775TH2M7YFIYEYRXDEGZ2OEATD3QKB4",
                            "type": "manage_data",
                            "type_i": 10,
                            "created_at": "2018-02-11T18:15:36Z",
                            "transaction_hash": "65d24932d779e484443128b4bb30c119f59ccd802ca758d580a5b5b3afbc24bd",
                            "name": "Johnny",
                            "value": "Q2FzaA=="
                            },

                    ]
                }
            }
    horizon, _ = stellar.get_current_network()
    endpoint = horizon + '/operations?limit=10&order=desc'
    with patch.object(stellar.utils.HTTP, 'get', return_value=opers) as get_mock:
        p = stellar.operations().fetch(order='desc')

        get_mock.assert_called_once_with(endpoint)

        i = 0
        records = opers["_embedded"]["records"]
        for e in p.entries():
            assert records[i]['id'] == e.opid
            assert records[i]['paging_token'] == e.paging_token
            assert records[i]['source_account'] == e.source_account
            assert records[i]['type_i'] == e.type_i
            assert datetime.datetime.strptime(records[i]['created_at'],\
                    '%Y-%m-%dT%H:%M:%SZ') == e.created_at
            if e.type_i == 0:
                assert records[i]['account'] == e.account
                assert records[i]['funder'] == e.funder
                assert records[i]['starting_balance'] == e.starting_balance
            elif e.type_i == 1:
                assert records[i]['amount'] == e.amount
                assert stellar.api.Asset(records[i]).asset_type == e.asset.asset_type
                assert stellar.api.Asset(records[i]).asset_code == e.asset.asset_code
                assert records[i]['from'] == e.from_account
                assert records[i]['to'] == e.to_account
            elif e.type_i == 2:
                assert records[i]['amount'] == e.amount
                assert stellar.api.Asset(records[i]).asset_type == e.asset.asset_type
                assert stellar.api.Asset(records[i]).asset_code == e.asset.asset_code
                assert stellar.api.Asset(records[i], 'send_').asset_type == e.send_asset.asset_type
                assert stellar.api.Asset(records[i], 'send_').asset_code == e.send_asset.asset_code
                assert records[i]['source_amount'] == e.source_amount
                assert records[i]['from'] == e.from_account
                assert records[i]['to'] == e.to_account
            elif e.type_i == 3 or  e.type_i == 4:
                if e.type_i == 3: assert records[i]['offer_id'] == e.offer_id
                assert records[i]['amount'] == e.amount
                assert records[i]['price'] == e.price
                assert stellar.api.Asset(records[i], 'buying_').asset_type == e.buying_asset.asset_type
                assert stellar.api.Asset(records[i], 'buying_').asset_code == e.buying_asset.asset_code
                assert stellar.api.Asset(records[i], 'selling_').asset_type == e.selling_asset.asset_type
                assert stellar.api.Asset(records[i], 'selling_').asset_code == e.selling_asset.asset_code
            elif e.type_i == 5:
                if 'low_threshold' in records[i]:
                    assert e.low_thresholds[0]  and e.low_thresholds[1] ==  records[i]['low_threshold']
                if 'med_threshold' in records[i]:
                    assert e.med_threshold[0] and e.med_threshold[1] ==  records[i]['med_threshold']
                if 'high_threshold' in records[i]:
                    assert e.high_threshold[0] and e.high_threshold[1] ==  records[i]['high_threshold']
                if 'inflation_dest' in records[i]:
                    assert e.inflation_dest[0] and e.inflation_dest[1] == records[i]['inflation_dest']
                if 'home_domain' in records[i]:
                    assert e.home_domain[0] and e.home_domain[1] == records[i]['home_domain']
                if 'signer_key' in records[i]:
                    assert e.signer_key[0] and e.signer_key[1] == records[i]['signer_key']
                if 'signer_weight' in records[i]:
                    assert e.signer_weight[0] and e.signer_weight[1] == int(records[i]['signer_weight'])
                if 'master_key_weight' in records[i]:
                    assert e.master_key_weight[0] and e.master_key_weight[1] == int(records[i]['master_key_weight'])
                if 'set_flags' in records[i]:
                    assert e.set_flags[0] and e.set_flags[1] == records[i]['set_flags']
                if 'clear_flags' in records[i]:
                    assert e.clear_flags[0] and e.clear_flags[1] == records[i]['clear_flags']
            elif e.type_i == 6 or e.type_i == 7:
                assert records[i]['trustor'] == e.trustor
                assert records[i]['trustee'] == e.trustee
                assert stellar.api.Asset(records[i]).asset_type == e.asset.asset_type
                assert stellar.api.Asset(records[i]).asset_code == e.asset.asset_code
                if e.type_i == 7:  assert records[i]['authorize'] == e.authorize
            elif e.type_i == 8:
                assert records[i]['account'] == e.account
                assert records[i]['into'] == e.merged_to
            elif e.type_i == 10:
                assert records[i]['name'] == e.key
                assert base64.b64decode(records[i]['value']) == e.value

            i += 1


def test_payments_fetch():
    stellar.setup_test_network()
    pays = {
            "_links": {
                "self": {
                    "href": "https://horizon.stellar.org/transactions?order=desc&limit=2&cursor=64034663848484864"
                    },
                "next": {
                    "href": "https://horizon.stellar.org/transactions?order=desc&limit=2&cursor=64034646668611584"
                    },
                "prev": {
                    "href": "https://horizon.stellar.org/transactions?order=asc&limit=2&cursor=64034659553513472"
                    }
                },
            "_embedded": {
                "records": [
                    {
                        "id": "10157597659137",
                        "paging_token": "10157597659137",
                        "source_account": "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H",
                        "type": "create_account",
                        "type_i": 0,
                        "created_at": "2017-03-20T19:50:52Z",
                        "transaction_hash": "17a670bc424ff5ce3b386dbfaae9990b66a2a37b4fbe51547e8794962a3f9e6a",
                        "starting_balance": "50000000.0000000",
                        "funder": "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H",
                        "account": "GBS43BF24ENNS3KPACUZVKK2VYPOZVBQO2CISGZ777RYGOPYC2FT6S3K"
                        },
                    {
                        "id": "10157597659138",
                        "paging_token": "10157597659138",
                        "source_account": "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H",
                        "type": "create_account",
                        "type_i": 0,
                        "created_at": "2017-03-20T19:50:52Z",
                        "transaction_hash": "17a670bc424ff5ce3b386dbfaae9990b66a2a37b4fbe51547e8794962a3f9e6a",
                        "starting_balance": "10000.0000000",
                        "funder": "GBRPYHIL2CI3FNQ4BXLFMNDLFJUNPU2HY3ZMFSHONUCEOASW7QC7OX2H",
                        "account": "GDO34SQXVOSNODK7JCTAXLZUPSAF3JIH4ADQELVIKOQJUWQ3U4BMSCSH"
                        }
                    ]
                }
            }
    horizon, _ = stellar.get_current_network()
    endpoint = horizon + '/payments?cursor=10157597659136&limit=2&order=desc'
    with patch.object(stellar.utils.HTTP, 'get', return_value=pays) as get_mock:
        p = stellar.payments().fetch(cursor='10157597659136', limit=2, order='desc')

        get_mock.assert_called_once_with(endpoint)
        assert len(p.entries()) == 2

        i = 0
        records = pays["_embedded"]["records"]
        for e in p.entries():
            assert records[i]['id'] == e.pid
            assert records[i]['paging_token'] == e.paging_token
            assert records[i]['source_account'] == e.source_account
            assert records[i]['type_i'] == e.type_i
            assert datetime.datetime.strptime(records[i]['created_at'],\
                    '%Y-%m-%dT%H:%M:%SZ') == e.created_at
            if e.type_i == 0:
                assert records[i]['starting_balance'] == e.amount
                assert records[i]['account'] == e.destination
            else:
                assert records[i]['amount'] == e.amount
                assert records[i]['to'] == e.destination
                assert stellar.api.Asset(records[i]).asset_type == e.asset.asset_type
                assert stellar.api.Asset(records[i]).asset_code == e.asset.asset_code
            i += 1

def test_effects_fetch():
    stellar.setup_test_network()
    pays = {
            "_links": {
                "self": {
                    "href": "https://horizon.stellar.org/transactions?order=desc&limit=2&cursor=64034663848484864"
                    },
                "next": {
                    "href": "https://horizon.stellar.org/transactions?order=desc&limit=2&cursor=64034646668611584"
                    },
                "prev": {
                    "href": "https://horizon.stellar.org/transactions?order=asc&limit=2&cursor=64034659553513472"
                    }
                },
            "_embedded": {
                "records": [
                    {
                        "id": "0031580615354621953-0000000003",
                        "paging_token": "31580615354621953-3",
                        "account": "GBB35Q6WMGSBNIG7IF3HXYSU6PNKTOO5OBO3ZDAMM7AAWJHNM2FVBAHD",
                        "type": "signer_created",
                        "type_i": 10,
                        "weight": 1,
                        "public_key": "GBB35Q6WMGSBNIG7IF3HXYSU6PNKTOO5OBO3ZDAMM7AAWJHNM2FVBAHD",
                        "key": ""                        
                        },
                    {
                        "id": "0031580615354621953-0000000002",
                        "paging_token": "31580615354621953-2",
                        "account": "GBS43BF24ENNS3KPACUZVKK2VYPOZVBQO2CISGZ777RYGOPYC2FT6S3K",
                        "type": "account_debited",
                        "type_i": 3,
                        "asset_type": "native",
                        "amount": "10000.0000000"
                        },
                    {
                        "id": "0031580615354621953-0000000001",
                        "paging_token": "31580615354621953-1",
                        "account": "GBB35Q6WMGSBNIG7IF3HXYSU6PNKTOO5OBO3ZDAMM7AAWJHNM2FVBAHD",
                        "type": "account_created",
                        "type_i": 0,
                        "starting_balance": "10000.0000000"
                        },
                    {
                        "id": "0031580606764683269-0000000001",
                        "paging_token": "31580606764683269-1",
                        "account": "GA4IBZJDA2K3JWC3L6XOKJLHCKES63HXVI2XCDN4SZ7FODVNL2QJY6GF",
                        "type": "account_credited",
                        "type_i": 2,
                        "asset_type": "credit_alphanum4",
                        "asset_code": "BTC",
                        "asset_issuer": "GA77B6GK5K3FH2YJ6I5VJ7VPFZKPBQUX2IIC2MJYAERQTGJI4VOPKRYJ",
                        "amount": "0.0017537"
                        },
                    {
                        "id": "0031580606764683268-0000000002",
                        "paging_token": "31580606764683268-2",
                        "account": "GA4IBZJDA2K3JWC3L6XOKJLHCKES63HXVI2XCDN4SZ7FODVNL2QJY6GF",
                        "type": "trade",
                        "type_i": 33,
                        "seller": "GDDNKUFTYHHBE45PK3RM3IICYGKK4RXCUKX5VNA5ZPWCXYXCUURI2DPX",
                        "offer_id": 90335,
                        "sold_amount": "0.0017467",
                        "sold_asset_type": "credit_alphanum4",
                        "sold_asset_code": "BTC",
                        "sold_asset_issuer": "GA77B6GK5K3FH2YJ6I5VJ7VPFZKPBQUX2IIC2MJYAERQTGJI4VOPKRYJ",
                        "bought_amount": "36.8120379",
                        "bought_asset_type": "native"
                        },
                    {
                            "id": "0031580477915664385-0000000001",
                            "paging_token": "31580477915664385-1",
                            "account": "GAJAFOU35T2MKOHH654B4H73R24SFDWY66PYS46YJOFYJVI462OFTKCI",
                            "type": "trustline_created",
                            "type_i": 20,
                            "asset_type": "credit_alphanum4",
                            "asset_code": "HUG",
                            "asset_issuer": "GCFN2S6H4BD5ABQNDGSUD3WTLISYPRSLI7UW3FKRHW7T7L7OLEZYJWU2",
                            "limit": "5000.0000000"
                            },
                    {
                            "id": "0031580404901220353-0000000003",
                            "paging_token": "31580404901220353-3",
                            "account": "GAJAFOU35T2MKOHH654B4H73R24SFDWY66PYS46YJOFYJVI462OFTKCI",
                            "type": "signer_created",
                            "type_i": 10,
                            "weight": 1,
                            "public_key": "GAJAFOU35T2MKOHH654B4H73R24SFDWY66PYS46YJOFYJVI462OFTKCI",
                            "key": ""
                            },
                    {
                            "id": "0031580331886776321-0000000001",
                            "paging_token": "31580331886776321-1",
                            "account": "GCFN2S6H4BD5ABQNDGSUD3WTLISYPRSLI7UW3FKRHW7T7L7OLEZYJWU2",
                            "type": "trustline_deauthorized",
                            "type_i": 24,
                            "trustor": "GCIKWDY2CYA3EWURO76ZBKVVHZT3XM4XJ6B5GU2KUD3MQNTKKBHSWVBV",
                            "asset_type": "credit_alphanum4",
                            "asset_code": "HUG"
                            },
                    {
                            "id": "0031580237397495809-0000000002",
                            "paging_token": "31580237397495809-2",
                            "account": "GCFN2S6H4BD5ABQNDGSUD3WTLISYPRSLI7UW3FKRHW7T7L7OLEZYJWU2",
                            "type": "signer_updated",
                            "type_i": 12,
                            "weight": 1,
                            "public_key": "GCFN2S6H4BD5ABQNDGSUD3WTLISYPRSLI7UW3FKRHW7T7L7OLEZYJWU2",
                            "key": ""
                            },
                    {
                            "id": "0031580237397495809-0000000001",
                            "paging_token": "31580237397495809-1",
                            "account": "GCFN2S6H4BD5ABQNDGSUD3WTLISYPRSLI7UW3FKRHW7T7L7OLEZYJWU2",
                            "type": "account_flags_updated",
                            "type_i": 6,
                            "auth_required_flag": True
                            },

                    ]
                }
            }
    horizon, _ = stellar.get_current_network()
    endpoint = horizon + '/effects?cursor=31580615354621953-3&limit=10&order=desc'
    with patch.object(stellar.utils.HTTP, 'get', return_value=pays) as get_mock:
        p = stellar.effects().fetch(cursor='31580615354621953-3', limit=10, order='desc')

        get_mock.assert_called_once_with(endpoint)
        assert len(p.entries()) == 10

        i = 0
        records = pays["_embedded"]["records"]
        for e in p.entries():
            assert records[i]['id'] == e.effectid
            assert records[i]['paging_token'] == e.paging_token
            assert records[i]['account'] == e.account
            assert records[i]['type_i'] == e.type_i
            i += 1

def test_orderbook_fetch():
    stellar.setup_test_network()
    book = {
            "bids": [
                {
                    "price_r": {
                        "n": 5000000,
                        "d": 47619
                        },
                    "price": "105.0001050",
                    "amount": "0.0000055"
                    },
                {
                    "price_r": {
                        "n": 100,
                        "d": 1
                        },
                    "price": "100.0000000",
                    "amount": "1.0000099"
                    }
                ],
            "asks": [
                {
                    "price_r": {
                        "n": 47619,
                        "d": 5000000
                        },
                    "price": "0.0095238",
                    "amount": "0.0000055"
                    },
                {
                    "price_r": {
                        "n": 1,
                        "d": 100
                        },
                    "price": "0.0100000",
                    "amount": "1.0000099"
                    }
                ],
            "base": {
                "asset_type": "credit_alphanum4",
                "asset_code": "CODR",
                "asset_issuer": "GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ"
                },
            "counter": {
                "asset_type": "native"
                }
            }

    horizon, _ = stellar.get_current_network()
    endpoint = horizon + '/order_book?selling_asset_type=native&buying_asset_type=credit_alphanum4&buying_asset_code=CODR&buying_asset_issuer=GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ'
    with patch.object(stellar.utils.HTTP, 'get', return_value=book) as get_mock:
        o = stellar.orderbook('native', ('CODR', 'GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ')).fetch()

        get_mock.assert_called_once_with(endpoint)

        assert o.asks[0][0] == '0.0000055'
        assert o.asks[0][1] == (47619, 5000000)
        assert o.asks[0][2] == '0.0095238'
        assert o.asks[1][0] == '1.0000099'
        assert o.asks[1][1] == (1, 100)
        assert o.asks[1][2] == '0.0100000'

        assert o.bids[0][0] == '0.0000055'
        assert o.bids[0][1] == (5000000, 47619)
        assert o.bids[0][2] == '105.0001050'
        assert o.bids[1][0] == '1.0000099'
        assert o.bids[1][1] == (100, 1)
        assert o.bids[1][2] == '100.0000000'

        assert o.base_asset.asset_type == 'credit_alphanum4'
        assert o.base_asset.asset_code == 'CODR'

        assert o.counter_asset.asset_type == 'native'


def test_assets_fetch():
    stellar.setup_test_network()
    assets = {
            "_links": {
                "self": {
                    "href": "https://horizon.stellar.org/transactions?order=desc&limit=2&cursor=64034663848484864"
                    },
                "next": {
                    "href": "https://horizon.stellar.org/transactions?order=desc&limit=2&cursor=64034646668611584"
                    },
                "prev": {
                    "href": "https://horizon.stellar.org/transactions?order=asc&limit=2&cursor=64034659553513472"
                    }
                },
            "_embedded": {
                "records": [
                    {
                        "_links": {
                            "toml": {
                                "href": ""
                                }
                            },
                        "asset_type": "credit_alphanum4",
                        "asset_code": "BTC",
                        "asset_issuer": "GAKTLYRXTVZITL7ZPWNY7TRVC4CZC5KFHG72RDNKGDRVYFGVQUJN2C3K",
                        "paging_token": "BTC_GAKTLYRXTVZITL7ZPWNY7TRVC4CZC5KFHG72RDNKGDRVYFGVQUJN2C3K_credit_alphanum4",
                        "amount": "0.0000000",
                        "num_accounts": 1,
                        "flags": {
                            "auth_required": False,
                            "auth_revocable": True,
                            }
                        },
                    {
                        "_links": {
                            "toml": {
                                "href": ""
                                }
                            },
                        "asset_type": "credit_alphanum4",
                        "asset_code": "BTC",
                        "asset_issuer": "GALOC23IRNNC2HR6QPS3XBPTNZ52OZMIDORN6DI3D7Y7HQDGPO2ZHA3R",
                        "paging_token": "BTC_GALOC23IRNNC2HR6QPS3XBPTNZ52OZMIDORN6DI3D7Y7HQDGPO2ZHA3R_credit_alphanum4",
                        "amount": "0.0000000",
                        "num_accounts": 1,
                        "flags": {
                            "auth_required": True,
                            "auth_revocable": False
                            }
                        }
                    ]
                }
            }

    horizon, _ = stellar.get_current_network()
    endpoint = horizon + '/assets?asset_code=BTC&cursor=BTC_GAHLVMIXWKU3ZXHOMNDBU5MR3QFFB5NGQPNER5JK7HP35JCSPBJ46XJH_credit_alphanum4&limit=2&order=desc'
    with patch.object(stellar.utils.HTTP, 'get', return_value=assets) as get_mock:
        p = stellar.assets(asset_code='BTC').fetch(cursor='BTC_GAHLVMIXWKU3ZXHOMNDBU5MR3QFFB5NGQPNER5JK7HP35JCSPBJ46XJH_credit_alphanum4', limit=2, order='desc')

        get_mock.assert_called_once_with(endpoint)

        assert len(p.entries()) == 2

        i = 0
        records = assets["_embedded"]["records"]
        for e in p.entries():
            assert records[i]['asset_type'] == e.asset.asset_type
            assert records[i]['asset_code'] == e.asset.asset_code
            assert records[i]['asset_issuer'] == e.asset.asset_issuer
            assert records[i]['paging_token'] == e.paging_token
            assert records[i]['amount'] == e.amount
            assert records[i]['num_accounts'] == e.num_accounts
            assert records[i]['flags']['auth_required'] == e.flags.auth_required
            assert records[i]['flags']['auth_revocable'] == e.flags.auth_revocable
            i += 1


def test_payment_path_fetch():
    stellar.setup_test_network()
    paypaths = {
            "_embedded": {
                "records": [
                    {
                        "source_asset_type": "credit_alphanum4",
                        "source_asset_code": "CODR",
                        "source_asset_issuer": "GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ",
                        "source_amount": "10.0000000",
                        "destination_asset_type": "credit_alphanum4",
                        "destination_asset_code": "CODR",
                        "destination_asset_issuer": "GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ",
                        "destination_amount": "10.0000000",
                        "path": []
                        },
                    {
                        "source_asset_type": "credit_alphanum4",
                        "source_asset_code": "CODR",
                        "source_asset_issuer": "GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ",
                        "source_amount": "750.0000000",
                        "destination_asset_type": "credit_alphanum4",
                        "destination_asset_code": "CODR",
                        "destination_asset_issuer": "GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ",
                        "destination_amount": "10.0000000",
                        "path": [
                            {
                                "asset_type": "credit_alphanum4",
                                "asset_code": "XPRN",
                                "asset_issuer": "GBDEVZYHBQJGWGZA2ZPG636XU7GNPHLZOFRMV4OPETVFTNDVF7YLEW3Y"
                                }
                            ]
                        }
                    ]
                }
            }
    horizon, _ = stellar.get_current_network()
    endpoint = horizon + '/paths?source_account=GDKGNWAE7N2KH6MLY5GGZUZWK775TH2M7YFIYEYRXDEGZ2OEATD3QKB4&destination_account=GBWF6NTCPGBROJIPF54XXYRLTUGBDLLORPFDK4FGQQ3IRI4T5PHCGVXV&destination_asset_type=credit_alphanum4&destination_asset_code=CODR&destination_asset_issuer=GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ&destination_amount=10'
    with patch.object(stellar.utils.HTTP, 'get', return_value=paypaths) as get_mock:
        p = stellar.find_payment_path('GDKGNWAE7N2KH6MLY5GGZUZWK775TH2M7YFIYEYRXDEGZ2OEATD3QKB4', 
                'GBWF6NTCPGBROJIPF54XXYRLTUGBDLLORPFDK4FGQQ3IRI4T5PHCGVXV', 
                ('CODR', 'GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ'), "10").fetch()

        get_mock.assert_called_once_with(endpoint)

