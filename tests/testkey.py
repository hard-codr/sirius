import stellar

def test_key_generation():
    secret, public = stellar.random_keypair()
    assert public == stellar.account_from_secret(secret)

def test_account_from_secret():
    seed = 'SABS6T5RZCOGXH6RZJM6BNHAN7KXVK6VKJRUPBW2KFABEWDBTIEPCRUO'
    public = 'GAO4R7CQGQAV2BEPPQ2LRQP3ANUFOJOBNDEM7AAVCWZA5IIUKIO2FKR5'
    account_id = stellar.account_from_secret(seed)
    assert public == account_id
