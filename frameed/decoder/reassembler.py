"""Reassemble ordered chunks into the final byte stream."""


def reassemble(data_chunks: dict[int, bytes], total_chunks: int) -> bytes:
    """
    Concatenate chunks 0..total_chunks-1 in order.
    Raises ValueError if any chunk is still missing after FEC.
    """
    missing = [i for i in range(total_chunks) if i not in data_chunks]
    if missing:
        raise ValueError(
            f"Cannot reassemble: {len(missing)} chunk(s) still missing: {missing[:10]}"
            + (" ..." if len(missing) > 10 else "")
        )
    return b''.join(data_chunks[i] for i in range(total_chunks))
