"""Optional AES-256-GCM encryption via pycryptodome."""
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes

SALT_SIZE  = 32   # bytes
NONCE_SIZE = 16   # bytes
TAG_SIZE   = 16   # bytes GCM auth tag
_PBKDF2_ITER = 100_000


def encrypt(data: bytes, password: str) -> bytes:
    """Return: FLAG(1) + salt(32) + nonce(16) + tag(16) + ciphertext.
    Leading FLAG=0x01 signals encryption is active."""
    salt  = get_random_bytes(SALT_SIZE)
    nonce = get_random_bytes(NONCE_SIZE)
    key   = PBKDF2(password.encode(), salt, dkLen=32, count=_PBKDF2_ITER)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(data)
    return b'\x01' + salt + nonce + tag + ciphertext


def decrypt(data: bytes, password: str) -> bytes:
    """Decrypt data produced by encrypt()."""
    if data[0:1] != b'\x01':
        raise ValueError("Data does not appear to be encrypted (missing flag byte).")
    offset = 1
    salt       = data[offset:offset + SALT_SIZE]; offset += SALT_SIZE
    nonce      = data[offset:offset + NONCE_SIZE]; offset += NONCE_SIZE
    tag        = data[offset:offset + TAG_SIZE];   offset += TAG_SIZE
    ciphertext = data[offset:]
    key = PBKDF2(password.encode(), salt, dkLen=32, count=_PBKDF2_ITER)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag)


def is_encrypted(data: bytes) -> bool:
    return len(data) > 0 and data[0:1] == b'\x01'
