"""Decrypt wrapper — delegates to encoder.encryptor."""
from frameed.encoder.encryptor import decrypt, is_encrypted


def maybe_decrypt(data: bytes, password: str | None) -> bytes:
    """Decrypt data if it is encrypted and a password is provided."""
    if is_encrypted(data):
        if password is None:
            raise ValueError("Data is encrypted but no password was provided.")
        return decrypt(data, password)
    if password is not None:
        print("[FrameED] WARNING: A password was provided but data does not appear encrypted.")
    return data
