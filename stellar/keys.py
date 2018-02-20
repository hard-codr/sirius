import os
import ed25519
import binascii
import crc16
import struct
import base64

KEY_TYPES = {
        'public' : '30',
        'seed' : '90'
        }

def random_keypair():
    """Generates pair of (secret,account-id). """
    seed = os.urandom(32)
    signing_key = ed25519.SigningKey(seed)
    verifying_key = signing_key.get_verifying_key()

    def encode_key(key_type, key):
        payload = binascii.a2b_hex(KEY_TYPES[key_type]) + key
        checksum = crc16.crc16xmodem(payload)
        checksum = struct.pack('H', checksum)
        return base64.b32encode(payload + checksum)

    return (encode_key('seed', signing_key.to_seed()), 
            encode_key('public', verifying_key.to_bytes()))

def account_from_secret(secret):
    """Returns account-id given the secret"""
    key = base64.b32decode(secret)
    checksum = struct.pack('H', crc16.crc16xmodem(key[0:-2]))
    keytype = binascii.a2b_hex(KEY_TYPES['seed'])
    if key[0] != keytype or key[-2:] != checksum:
        raise Exception('Invalid Secret Key')

    signing_key = ed25519.SigningKey(key[1:-2])
    payload = binascii.a2b_hex(KEY_TYPES['public']) + signing_key.get_verifying_key().to_bytes()
    checksum = crc16.crc16xmodem(payload)
    checksum = struct.pack('H', checksum)
    return base64.b32encode(payload + checksum)
