"""
FEC reconstructor: uses PARITY frames to recover missing DATA chunks.

For each parity group of size G:
  - If exactly 1 DATA frame is missing → recover via XOR(parity, *received).
  - If 0 frames are missing → parity frame is unused.
  - If >1 frames are missing → unrecoverable (logged as error).
"""
from __future__ import annotations
from frameed.encoder.fec import recover_missing_chunk


def reconstruct(
    data_chunks: dict[int, bytes],   # chunk_id → raw_payload (DATA frames)
    parity_map:  dict[int, bytes],   # group_start → raw parity payload
    total_chunks: int,
    parity_group: int,
) -> dict[int, bytes]:
    """
    Attempt to fill gaps in data_chunks using parity_map.
    Returns an updated data_chunks dict.
    """
    recovered = dict(data_chunks)

    for group_start, parity_payload in parity_map.items():
        group_ids = list(range(group_start, min(group_start + parity_group, total_chunks)))
        group = [recovered.get(i) for i in group_ids]
        missing = [i for i, c in zip(group_ids, group) if c is None]

        if len(missing) == 0:
            continue  # no recovery needed
        if len(missing) == 1:
            try:
                fixed = recover_missing_chunk(group, parity_payload)
                recovered[missing[0]] = fixed
                print(f"[FrameED] Recovered missing chunk {missing[0]} via XOR parity.")
            except Exception as exc:
                print(f"[FrameED] WARNING: Could not recover chunk {missing[0]}: {exc}")
        else:
            print(f"[FrameED] WARNING: {len(missing)} missing chunks in group {group_start} — unrecoverable.")

    return recovered
