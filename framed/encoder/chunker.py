"""Split processed payload bytes into fixed-size raw chunks."""
import math


def chunk_data(data: bytes, chunk_size: int) -> list[bytes]:
    """Split data into chunks of at most chunk_size bytes."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]


def num_chunks(data_len: int, chunk_size: int) -> int:
    return math.ceil(data_len / chunk_size) if data_len > 0 else 1
