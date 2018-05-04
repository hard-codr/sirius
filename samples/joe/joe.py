#joe - a simple stellar trading CLI 

import getpass
import os
import os.path
import sys
import stellar
from fractions import Fraction

MAX_LIMIT = 922337203685.4775807

BASEPATH = os.getcwd()

def add_user_id(user):
    with open('%s/.user.pubic_key' % BASEPATH, 'w') as f:
        f.write(user)

def remove_user_id():
    os.remove('%s/.user.pubic_key' % BASEPATH)

def _get_user_id():
    user = None
    userfile = '%s/.user.pubic_key' % BASEPATH
    if not os.path.isfile(userfile):
        print 'User not found. Add the user first'
        return (False, user)

    with open(userfile, 'r') as f:
        user = f.readlines()[0]
        
    if not user or len(user) < 56:
        print 'Incorrect user. Corrupted user file %s, add user again' % userfile
        return (False, user)

    return (True, user)

def account_details():
    r = _get_user_id()
    if not r[0]:
        return False
    user = r[1]

    try:
        account = stellar.account(user).fetch()
    except:
        print 'Account doesn\'t exist'
        return False

    if account:
        print 'Account : %s' % account.account_id
        print 'Balances: '
        for b in account.balances:
            print '\t%s %s' % (b.balance, b.asset.asset_code)
        return True
    else:
        print 'Account doesn\'t exist'
        return False

def get_user_secret():
    return getpass.getpass('User secret:')

def add_trust(asset, asset_issuer, skipAdd=False):
    is_added = True
    if not skipAdd:
        print 'Adding trust for asset %s on stellar' % asset
        user = get_user_secret()
        with stellar.new_transaction(user, memo='Add Trust %s' % asset) as t:
            t.create_or_update_trust(asset=(asset, asset_issuer), limit=MAX_LIMIT)

        if t.is_success():
            print 'Trust successfully added'
            print t.result()
        else:
            is_added = False
            print t.errors()

    if is_added:
        with open('%s/%s.asset' % (BASEPATH, asset), 'w') as f:
            f.write(asset_issuer)
        return True
    else:
        return False

def remove_trust(asset, asset_issuer):
    print 'Removing trust for asset %s on stellar' % asset
    user = get_user_secret()
    with stellar.new_transaction(user, memo='Remove Trust %s' % asset) as t:
        t.remove_trust(asset=(asset, asset_issuer))

    if t.is_success():
        os.remove('%s/%s.asset' % (BASEPATH, asset))
        print 'Trust successfully removed'
        print t.result()
    else:
        print t.errors()

def _get_trusted_asset(asset):
    assetfile = '%s/%s.asset' % (BASEPATH, asset)
    if not os.path.isfile(assetfile):
        print 'Incorrect asset. Add the trust for this asset first'
        return (False, ())

    asset_issuer = None
    with open(assetfile, 'r') as f:
        asset_issuer = f.readlines()[0]

    if not asset_issuer or len(asset_issuer) < 56:
        print 'Incorrect asset. Corrupted asset file %s, add trust again with skipAdd' % assetfile
        return (False, ())

    return (True, (asset, asset_issuer))

def buy_asset_against_native(asset, amount, price, offer_id=0):
    r = _get_trusted_asset(asset)
    if not r[0]:
        return False
    trusted_asset = r[1]

    try:
        amount = float(amount)
        price = float(price)
    except:
        print 'Incorrect amount or price. Must be decimal values'
        return False

    #res = Fraction(price).limit_denominator()

    cny_amount = amount
    amount = amount*price
    price = 1.0/price
    res = Fraction(price).limit_denominator()

    print 'Buying %s CNY at price (%s %s/ %s XLM)' % (cny_amount,\
            res.numerator, asset, res.denominator)
    user = get_user_secret()

    with stellar.new_transaction(user, memo='Buy %s' % asset) as t:
        if offer_id == 0:
            t.add_offer(sell_amount=str(amount), sell_asset='native',\
                    buy_asset=trusted_asset, price=(res.numerator, res.denominator))
        else:
            t.update_offer(offer_id=int(offer_id), sell_amount=str(amount),\
                    sell_asset='native', buy_asset=trusted_asset,\
                    price=(res.numerator, res.denominator))

    if t.is_success():
        print 'Offer added successfully'
        print t.result()
        return True
    else:
        print t.errors()
        return False

def sell_asset_against_native(asset, amount, price, offer_id=0):
    r = _get_trusted_asset(asset)
    if not r[0]:
        return False
    trusted_asset = r[1]

    try:
        amount = float(amount)
        price = float(price)
    except:
        print 'Incorrect amount or price. Must be decimal values'
        return False

    res = Fraction(price).limit_denominator()

    print 'Selling %s %s at price (%s XLM/ %s %s)' % (amount, asset, res.numerator, res.denominator, asset)
    user = get_user_secret()

    with stellar.new_transaction(user, memo='Sell %s' % asset) as t:
        if offer_id == 0:
            t.add_offer(sell_amount=str(amount), sell_asset=trusted_asset,\
                    buy_asset='native', price=(res.numerator, res.denominator))
        else:
            t.update_offer(offer_id=int(offer_id), sell_amount=str(amount),\
                    sell_asset=trusted_asset, buy_asset='native',\
                    price=(res.numerator, res.denominator))

    if t.is_success():
        print 'Offer added successfully'
        print t.result()
        return True
    else:
        print t.errors()
        return False

def list_offer(asset):
    r = _get_trusted_asset(asset)
    if not r[0]:
        return False
    trusted_asset = r[1]

    r = _get_user_id()
    if not r[0]:
        return False
    user = r[1]

    #in case account doesnt exist then this call will fail
    try:
        stellar.account(user).fetch()
    except:
        print 'Account doesn\'t exist'
        return False

    offers = stellar.account(user).offers().fetch()
    for offer in offers.entries():
        if offer.selling.asset_code == trusted_asset[0] and offer.selling.asset_issuer == trusted_asset[1]:
            print '[Offer %s] selling = %s %s, buying = %s, price = %s' %\
                    (offer.offerid, offer.amount, offer.selling.asset_code,\
                            offer.buying.asset_code, offer.price)

        if offer.buying.asset_code == trusted_asset[0] and offer.buying.asset_issuer == trusted_asset[1]:
            print '[Offer %s] selling = %s %s, buying = %s, price = %s' %\
                    (offer.offerid, offer.amount, offer.selling.asset_code,\
                            offer.buying.asset_code, offer.price)

    return True

def remove_offer(offer_id):
    r = _get_user_id()
    if not r[0]:
        return False
    user = r[1]

    try:
        stellar.account(user).fetch()
    except:
        print 'Account doesn\'t exist'
        return False

    offers = stellar.account(user).offers().fetch()
    offer_to_cancel = None
    for offer in offers.entries():
        if str(offer.offerid) == str(offer_id):
            offer_to_cancel = offer
    
    if not offer_to_cancel:
        print 'Offer %s not found' % offer_id
        return False

    selling = 'native' if offer_to_cancel.selling.asset_code == 'XLM'\
            else (offer_to_cancel.selling.asset_code, offer_to_cancel.selling.asset_issuer)
    buying =  'native' if offer_to_cancel.buying.asset_code == 'XLM'\
            else (offer_to_cancel.buying.asset_code, offer_to_cancel.buying.asset_issuer)

    print 'Removing offer %s for selling %s buying %s' % (offer_id, selling, buying)
    user = get_user_secret()

    with stellar.new_transaction(user, memo='Cancel offer') as t:
        t.remove_offer(offer_id=int(offer_id), sell_asset=selling, buy_asset=buying)

    if t.is_success():
        print 'Offer removed successfully'
        print t.result()
        return True
    else:
        print t.errors()
        return False

if __name__ == '__main__':
    if len(sys.argv) > 0 and sys.argv[0] == 'joe.py':
        args = sys.argv[1:]
    else:
        args = sys.argv

    is_test = False
    for a in args:
        if a == '--test':
            is_test = True
            break

    if is_test:
        stellar.setup_test_network()
        args.remove('--test')
    else:
        stellar.setup_public_network()

    if len(args) < 1 or args[0] == 'help':
        print 'joe.py <operation> <params>'
        print 'where operations can be:'
        print ' - add_user <user-public-key>'
        print ' - remove_user'
        print ' - account'
        print ' - trust <code> <issuer>'
        print ' - detrust <code>'
        print ' - buy <asset> <amount> <price>'
        print ' - sell <asset> <amount> <price>'
        print ' - list_offers <asset>'
        print ' - remove_offer <offer-id>'
        sys.exit(-1)

    oper = args[0]

    if oper == 'add_user':
        if len(args) < 2:
            print 'joe add_user account-id'
            sys.exit(-1)
        user = args[1]
        if not add_user_id(user):
            sys.exit(-1)
    elif oper == 'remove_user':
        if not remove_user_id():
            sys.exit(-1)
    elif oper == 'account':
        if not account_details():
            sys.exit(-1)
    elif oper == 'trust':
        suc = False
        if len(args) == 3:
            suc = add_trust(args[1], args[2])
        elif len(args) == 4:
            suc = add_trust(args[1], args[2], 
                    True if args[3] == '--skipAdd' else False)
        else:
            print 'joe trust asset_code asset_issuer [--skipAdd]'
        if not suc:
            sys.exit(-1)
    elif oper == 'detrust':
        suc = False
        if len(args) == 3:
            suc = remove_trust(args[1], args[2])
        else:
            print 'joe detrust asset_code asset_issuer'
        if not suc:
            sys.exit(-1)
    elif oper == 'buy':
        suc = False
        if len(args) == 4:
            suc = buy_asset_against_native(args[1], args[2],\
                    args[3])
        elif len(args) == 5:
            suc = buy_asset_against_native(args[1], args[2],\
                    args[3], args[4])
        else:
            print 'joe buy asset_code amount price [offer_id]'
        if not suc:
            sys.exit(-1)
    elif oper == 'sell':
        suc = False
        if len(args) == 4:
            suc = sell_asset_against_native(args[1], args[2],\
                    args[3])
        elif len(args) == 5:
            suc = sell_asset_against_native(args[1], args[2],\
                    args[3], args[4])
        else:
            print 'joe sell asset_code amount price [offer_id]'
        if not suc:
            sys.exit(-1)
    elif oper == 'list_offers':
        suc = False
        if len(args) == 2:
            suc = list_offer(args[1])
        else:
            print 'joe list_offers asset_code'
        if not suc:
            sys.exit(-1)
    elif oper == 'remove_offer':
        suc = False
        if len(args) == 2:
            suc = remove_offer(args[1])
        else:
            print 'joe remove_offer offer_id'
        if not suc:
            sys.exit(-1)
    else:
        print 'Operation not supported. Try joe help'
