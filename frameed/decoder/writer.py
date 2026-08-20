"""Write the final recovered bytes to disk."""
import os
from pathlib import Path


def write_output(data: bytes, filename: str, output_dir: str) -> str:
    """Write data to output_dir/filename. Creates output_dir if needed."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / filename
    # Avoid overwriting: append _recovered if file already exists
    if out_path.exists():
        stem = out_path.stem
        suffix = out_path.suffix
        out_path = out_dir / f"{stem}_recovered{suffix}"
    out_path.write_bytes(data)
    print(f"[FrameED] Output written -> {out_path}  ({len(data):,} bytes)")
    return str(out_path)
