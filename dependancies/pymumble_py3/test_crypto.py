'''
Ported from Mumble src/tests/TestCrypt/TestCrypt.cpp

=============================================================

Copyright 2005-2020 The Mumble Developers. All rights reserved.
Use of this source code is governed by a BSD-style license
that can be found in the LICENSE file at the root of the
Mumble source tree or at <https://www.mumble.info/LICENSE>.
'''

import pytest

from .crypto import CryptStateOCB2, AES_BLOCK_SIZE, EncryptFailedException, DecryptFailedException
from .crypto import ocb_encrypt, ocb_decrypt


@pytest.fixture()
def rawkey():
    return bytes((0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0a,0x0b,0x0c,0x0d,0x0e,0x0f))


@pytest.fixture()
def nonce():
    return bytes((0xff, 0xee, 0xdd, 0xcc, 0xbb, 0xaa, 0x99, 0x88, 0x77, 0x66, 0x55, 0x44, 0x33, 0x22, 0x11, 0x00))


def test_reverserecovery():
    enc = CryptStateOCB2()
    dec = CryptStateOCB2()
    enc.gen_key()

    # For our testcase, we're going to FORCE iv
    enc.encrypt_iv = bytes((0x55,) * AES_BLOCK_SIZE)
    dec.set_key(enc.raw_key, enc.decrypt_iv, enc.encrypt_iv)

    secret = "abcdefghi".encode('ascii')

    crypted = [enc.encrypt(secret) for _ in range(128)]

    i = 0
    for crypt in reversed(crypted[-30:]):
        print(i)
        i += 1
        dec.decrypt(crypt, len(secret))
    for crypt in reversed(crypted[:-30]):
        with pytest.raises(DecryptFailedException):
            dec.decrypt(crypt, len(secret))
    for crypt in reversed(crypted[-30:]):
        with pytest.raises(DecryptFailedException):
            dec.decrypt(crypt, len(secret))

    # Extensive replay attack test
    crypted = [enc.encrypt(secret) for _ in range(512)]

    for crypt in crypted:
        decr = dec.decrypt(crypt, len(secret))
    for crypt in crypted:
        with pytest.raises(DecryptFailedException):
            dec.decrypt(crypt, len(secret))


def test_ivrecovery():
    enc = CryptStateOCB2()
    dec = CryptStateOCB2()
    enc.gen_key()

    # For our testcase, we're going to FORCE iv
    enc.encrypt_iv = bytes((0x55,) * AES_BLOCK_SIZE)
    dec.set_key(enc.raw_key, enc.decrypt_iv, enc.encrypt_iv)

    secret = "abcdefghi".encode('ascii')

    crypted = enc.encrypt(secret)

    # Can decrypt
    decr = dec.decrypt(crypted, len(secret))
    # ... correctly.
    assert secret == decr

    # But will refuse to reuse same IV.
    with pytest.raises(DecryptFailedException):
        dec.decrypt(crypted, len(secret))

    # Recover from lost packet.
    for i in range(16):
        crypted = enc.encrypt(secret)
    decr = dec.decrypt(crypted, len(secret))

    # Wraparound.
    for i in range(128):
        dec.uiLost = 0
        for j in range(15):
            crypted = enc.encrypt(secret)
        decr = dec.decrypt(crypted, len(secret))
        assert dec.uiLost == 14

    assert enc.encrypt_iv == dec.decrypt_iv

    # Wrap too far
    for i in range(257):
        crypted = enc.encrypt(secret);

    with pytest.raises(DecryptFailedException):
        dec.decrypt(crypted, len(secret))

    # Sync it
    dec.decrypt_iv = enc.encrypt_iv
    crypted = enc.encrypt(secret)

    decr = dec.decrypt(crypted, len(secret))

def test_testvectors(rawkey):
    # Test vectors are from draft-krovetz-ocb-00.txt
    cs = CryptStateOCB2()
    cs.set_key(rawkey, rawkey, rawkey)

    _, tag = ocb_encrypt(cs._aes, bytes(), rawkey)

    blanktag = bytes((0xBF,0x31,0x08,0x13,0x07,0x73,0xAD,0x5E,0xC7,0x0E,0xC6,0x9E,0x78,0x75,0xA7,0xB0))
    assert len(blanktag) == AES_BLOCK_SIZE

    assert tag == blanktag

    source = bytes(range(40))
    crypt, tag = ocb_encrypt(cs._aes, source, rawkey)
    longtag = bytes((0x9D,0xB0,0xCD,0xF8,0x80,0xF7,0x3E,0x3E,0x10,0xD4,0xEB,0x32,0x17,0x76,0x66,0x88))
    crypted = bytes((0xF7,0x5D,0x6B,0xC8,0xB4,0xDC,0x8D,0x66,0xB8,0x36,0xA2,0xB0,0x8B,0x32,0xA6,0x36,0x9F,0x1C,0xD3,0xC5,0x22,0x8D,0x79,0xFD,
                     0x6C,0x26,0x7F,0x5F,0x6A,0xA7,0xB2,0x31,0xC7,0xDF,0xB9,0xD5,0x99,0x51,0xAE,0x9C))

    assert tag == longtag
    assert crypt[:len(crypted)] == crypted


def test_authcrypt(rawkey, nonce):
    cs = CryptStateOCB2()
    for ll in range(128):
        cs.set_key(rawkey, nonce, nonce)
        src = bytes((i + 1 for i in range(ll)))

        encrypted, enctag = ocb_encrypt(cs._aes, src, nonce)
        decrypted, dectag = ocb_decrypt(cs._aes, encrypted, nonce, len(src))

        assert enctag == dectag
        assert src == decrypted


def test_xexstarAttack(rawkey, nonce):
    ''' Test prevention of the attack described in section 4.1 of https://eprint.iacr.org/2019/311 '''
    cs = CryptStateOCB2()
    cs.set_key(rawkey, nonce, nonce)

    # Set first block to `len(secondBlock)`
    # Set second block to arbitrary value
    src = bytearray(AES_BLOCK_SIZE) + bytearray([42] * AES_BLOCK_SIZE)
    src[AES_BLOCK_SIZE - 1] = AES_BLOCK_SIZE * 8
    print(src)

    with pytest.raises(EncryptFailedException):
        ocb_encrypt(cs._aes, src, nonce)
    encrypted, enctag = ocb_encrypt(cs._aes, src, nonce, insecure=True)

    # Perform the attack
    encrypted = bytearray(encrypted)
    enctag = bytearray(enctag)
    encrypted[AES_BLOCK_SIZE - 1] ^= AES_BLOCK_SIZE * 8
    for i in range(AES_BLOCK_SIZE):
        enctag[i] = src[AES_BLOCK_SIZE + i] ^ encrypted[AES_BLOCK_SIZE + i]

    with pytest.raises(DecryptFailedException):
        dc, dct = ocb_decrypt(cs._aes, encrypted, nonce, AES_BLOCK_SIZE)
        print(dc, dct, enctag == dct)
    decrypted, dectag = ocb_decrypt(cs._aes, encrypted, nonce, AES_BLOCK_SIZE, insecure=True)

    # Verify forged tag (should match if attack is properly implemented)
    assert enctag == dectag


def test_tamper(rawkey, nonce):
    cs = CryptStateOCB2()
    cs.set_key(rawkey, nonce, nonce)

    msg = "It was a funky funky town!".encode('ascii')
    encrypted = bytearray(cs.encrypt(msg))

    for i in range(len(msg) * 8):
        encrypted[i // 8] ^= 1 << (i % 8)
        with pytest.raises(DecryptFailedException):
            cs.decrypt(encrypted, len(msg))
        encrypted[i // 8] ^= 1 << (i % 8)
    decrypted = cs.decrypt(encrypted, len(msg))
