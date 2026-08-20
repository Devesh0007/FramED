# FrameED — Visual Data-Storage Protocol

> **Any file → black/white video → byte-for-byte recovery.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org)

## How it works

```
File → Compress (zstd) → [Encrypt (AES-256-GCM)] → Chunk → RS-ECC encode
  → Self-describing frames → n×n pixel B&W cells → Lossless FFV1 video
```

Each video frame is **self-describing** — it carries a full header (magic, version,
frame ID, file UUID, chunk ID, payload length, CRC32) so the decoder doesn't blindly
assume ordering.  Two layers of error correction protect every byte:

| Layer | What it does |
|---|---|
| **Reed-Solomon ECC** | Corrects up to 8 random byte-errors per 255-byte RS block (in-frame) |
| **XOR parity frames** | Recovers any 1 missing frame per group of N frames (cross-frame) |

## Encoding modes

| Mode | Cell size | Throughput | Best for |
|---|---|---|---|
| `archive` | 4×4 px | ~437 KB/s @ 30 FPS | Pristine MP4/AVI storage |
| `optical` | 8×8 px | ~80 KB/s @ 24 FPS | Survives re-encoding, camera capture |

## Installation

```bash
pip install -r requirements.txt
# FFmpeg must be on PATH (https://ffmpeg.org/download.html)
```

## Usage

```bash
# Encode
python main.py encode photo.jpg output.avi
python main.py encode document.pdf output.avi --mode optical
python main.py encode secret.zip output.avi --password "my-passphrase"

# Decode
python main.py decode output.avi ./recovered/
python main.py decode output.avi ./recovered/ --password "my-passphrase"
```

## Run tests

```bash
pytest tests/ -v
```

> Tests that require FFmpeg/OpenCV skip automatically if those tools aren't found.

## Frame protocol

```
┌──────────────────────────────────────────────────────────┐
│ SYNC BORDER (checkerboard, 2-cell wide)                  │
│  ┌────────────────────────────────────────────────────┐  │
│  │ HEADER (39 bytes)                                  │  │
│  │  MAGIC(4) VERSION(1) TYPE(1) FRAME_ID(4)           │  │
│  │  TOTAL_FRAMES(4) FILE_ID(16) CHUNK_ID(4)           │  │
│  │  PAYLOAD_LEN(4) FLAGS(1)                           │  │
│  ├────────────────────────────────────────────────────┤  │
│  │ RS-ECC PAYLOAD (variable)                          │  │
│  ├────────────────────────────────────────────────────┤  │
│  │ CRC32 of raw payload (4 bytes)                     │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

## Project structure

```
frameed/
├── config.py            # Protocol constants & mode configs
├── utils.py             # Bit packing, CRC32
├── pipeline.py          # encode_file() / decode_file()
├── encoder/
│   ├── compressor.py    # zstd compression
│   ├── encryptor.py     # AES-256-GCM
│   ├── chunker.py       # chunk splitter
│   ├── fec.py           # RS ECC + XOR parity
│   ├── frame_builder.py # assemble frame blobs
│   ├── renderer.py      # blob → PIL B&W image
│   └── video_writer.py  # PIL frames → FFV1 AVI
└── decoder/
    ├── video_reader.py       # video → numpy frames
    ├── frame_parser.py       # pixel sampling + header parse
    ├── fec_reconstructor.py  # XOR parity recovery
    ├── reassembler.py        # ordered chunk join
    ├── decryptor.py          # AES decrypt
    ├── decompressor.py       # zstd decompress
    └── writer.py             # write output file
```

## ⚠️ Important notes

- **Lossless only** (archive mode): do not re-encode with H.264 default settings.
- **Optical mode** tolerates moderate re-encoding / camera capture, but homography-corrected
  alignment (rotation/resize recovery) is a planned future enhancement.
- Losing your **encryption password** means the data is **permanently unrecoverable**.
"# FrameED" 
