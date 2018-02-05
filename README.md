# Sirius: Stellar API for Humans

Sirius is Python SDK for Stellar. This library tries to make Stellar API favorable 
for human consumption, with no known side effects.

Following are some examples of typical usage of Sirius:

```python
>>> stellar.account('GBS4..6S3K').fetch() 
Account(id=GAEE..IB4V..,seq=28515937145585674,balances=[Balance(9855.9998800 XLM)])

>>> stellar.account('GBS4..6S3K').operations().fetch(limit=1).entries()
[Operation(id=28515937145589761,account=GBS4..6S3K,type=create_account)]

>>> with stellar.new_transaction('SEED..5KEE', memo='awain') as t:
...     t.pay(account='GBS4..6S3K', amount='42.01')
...     # remove existing offer for buying BTC
...     t.remove_offer(offer_id=12891, sell_asset='native', buy_asset=('BTC', 'GADE..ED87'))
...     # add new offer to buy BTC
...     t.add_offer(sell_amount='10.00', sell_asset='native', buy_asset=('BTC', 'GADE..ED87'), price=(1, 10000))
...

```

##  Why so Sirius?
Sirius is inspired by very well designed 'requests' HTTP library. Following
are some of the reason I created this library.

### Comparison with current libraries
Current best known Python SDK does not have required ergonomics, and bit hassle to use. 

E.g. to create new account you need to do following:
```python
oldAccountSeed = "SCVLSUGYEAUC4MVWJORB63JBMY2CEX6ATTJ5MXTENGD3IELUQF4F6HUB"
newAccountAddress = "XXX"
amount = '25' # Any amount higher than 20
kp = Keypair.from_seed(oldAccountSeed)
horizon = horizon_livenet()
asset = Asset("XLM")
# create op 
op = CreateAccount({
    'destination': newAccountAddress,
    'starting_balance': amount
})
# create a memo
msg = TextMemo('test-account')
# get sequence of new account address
sequence = horizon.account(kp.address()).get('sequence')
# construct the transaction
tx = Transaction(
    source=kp.address().decode(),
    opts={
        'sequence': sequence,
        #'timeBounds': [],
        'memo': msg,
        #'fee': 100,
        'operations': [
            op,
        ],
    },
)
# build envelope
envelope = Te(tx=tx, opts={"network_id": "PUBLIC"})
# sign 
envelope.sign(kp)
# submit
xdr = envelope.xdr()
response = horizon.submit(xdr)
```

Whereas in Sirius you can simply do:
```python
old_account_seed = "SCVLSUGYEAUC4MVWJORB63JBMY2CEX6ATTJ5MXTENGD3IELUQF4F6HUB"
new_account_address = "XXX"
amount = '5'
#following statement takes care of retrieving current sequence for account
#and signing and submitting at the end of with-block
with stellar.new_transaction(old_account_seed, memo='test-account') as t:
    t.create_account(new_account_address, amount)
if t.is_success():
    print t.result()
else:
    print t.errors()
```

If you don't want to use with-statement then you can also chain multiple 
operation as follows and submit transaction:
```python
account_seed = "SCVLSUGYEAUC4MVWJORB63JBMY2CEX6ATTJ5MXTENGD3IELUQF4F6HUB"
to_account1 = "GDKGNWAE7N2KH6MLY5GGZUZWK775TH2M7YFIYEYRXDEGZ2OEATD3QKB4"
to_account2 = "GDZ4R34MNVITLNZ4KVKBEANJU3UZZFZZLOX7ZVU5AWI7FEL5A6JWDM24"
usd_issuer = "GDUWG5CZ6YJNWOPQB33DOKWVWSNHJAWPWOUNAEBVTM7QRJ66NGFYEFAJ"

trx = stellar.new_transaction(account_seed, 'test-pay')
                .pay(to_account1, "10.01") #by default, payment is done in native asset
                .pay(to_account2, "42.42", asset=('USD', usd_issuer)) #or you can specify asset
                .submit()
if trx.is_success():
    print trx.result()
else:
    print trx.errors()
```

### Ease of use
Some of the stellar APIs are confusing to use.  For example, to add offer and to 
remove offer there is the same API, i.e. MANAGE_OFFER with special meaning to the 
input parameters. Sirius simplifies those API and tries to create self-explanatory
APIs and handles needed complexity internally.

## Install
To install with pip just type
```bash
pip install git+https://github.com/hard-codr/sirius
```

## Planned Features
1. Write extensive test cases
2. Error handling
3. Write functions for key generation
4. Good documentation
5. Lots of bug fixes
