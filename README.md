# FramED — High-Density Visual Data-Storage Protocol

> **Transform any file into high-density video containers with 100% byte-for-byte lossless recovery.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tests/)
[![Security: AES-256-GCM](https://img.shields.io/badge/security-AES--256--GCM-orange.svg)](framed/encoder/encryptor.py)

**FramED** is a visual data-storage protocol and streaming engine that serializes arbitrary digital files (binaries, archives, documents, media) into video frame sequences. By mapping binary data directly across spatial color channels and incorporating self-describing framing headers, cryptographic authentication, and cross-frame XOR parity redundancy, FramED turns video formats into reliable, high-capacity cold storage and transport media.

---

## ⚡ How It Works

```
ENCODING PIPELINE:
  Input File
    │
    ▼
  Zstandard (zstd) Compression (multithreaded, embedded metadata)
    │
    ▼
  [Optional AES-256-GCM Encryption] (PBKDF2 100k rounds + 256-bit key)
    │
    ▼
  Dynamic Chunk Splitter (mode-aware byte segmentation)
    │
    ▼
  XOR Parity Generator (vectorized cross-frame parity groups)
    │
    ▼
  Frame Assembler (39-byte header + payload + CRC32 checksum)
    │
    ▼
  NumPy / PIL Rasterizer (checkerboard sync borders + RGB/binary cell grid)
    │
    ▼
  FFmpeg / OpenCV Streamer (zero-RAM generator piped to video container)
    │
    ▼
  Lossless / Platform-Resilient Video (.avi / .mp4)


DECODING PIPELINE:
  Video Container (.avi / .mp4)
    │
    ▼
  OpenCV Frame Stream Generator (on-the-fly frame extraction)
    │
    ▼
  Dynamic Rescaling & Center-Cell Sampling (handles platform downscaling)
    │
    ▼
  Header Parser & CRC32 Validation (self-describing manifest & data frames)
    │
    ▼
  FEC Reconstructor (recovers dropped/corrupted frames via XOR parity)
    │
    ▼
  Chunk Reassembler (ordered concatenation & padding truncation)
    │
    ▼
  [Optional AES-256-GCM Decryption] (authenticated cipher validation)
    │
    ▼
  Zstandard Decompressor (restores original file name & exact bytes)
    │
    ▼
  Byte-for-Byte Recovered File
```

---

## 🚀 Encoding Modes

FramED provides three specialized profiles engineered for distinct deployment scenarios:

| Mode | Cell Size | Resolution | FPS | Channels / Depth | Usable Frame Capacity | Raw Throughput | Target Use Case |
|---|---|---|---|---|---|---|---|
| **`archive`** | 1×1 px | 3840×2160 (4K UHD) | 60 | 3 (RGB 24-bit) | **24.17 MB** / frame | **~1.35 GB/s** | Local archival, high-density SSD/HDD backup, lossless FFV1 |
| **`optical`** | 8×8 px | 1920×1080 (1080p FHD) | 30 | 3 (RGB 24-bit) | **75.86 KB** / frame | **~2.17 MB/s** | Screen recording, physical camera capture, projector playback |
| **`youtube`** | 2×2 px | 1920×1080 (1080p FHD) | 60 | 3 (1-bit binary) | **183.26 KB** / frame | **~10.49 MB/s** | Video hosting uploads, lossy H.264/CRF 28, chroma subsampling resilience |

### Which Mode Should You Use?
- **Use `archive`** when storing files locally or transferring via lossless video containers (`FFV1` or `libx264rgb` CRF 0). Maximizes storage density (up to ~24 MB per frame, ~86 GB per hour of video).
- **Use `youtube`** when sharing files over streaming platforms or social media (YouTube, Vimeo). Engineered specifically with binary high-contrast states (0 vs 255) and 2×2 cells to survive destructive lossy compression, 4:2:0 chroma subsampling, and platform resolution downscaling.
- **Use `optical`** when capturing frames from physical monitors using smartphone cameras or webcams, where large 8×8 cell geometry resists lens blur and optical distortion.

---

## 📦 Installation

### 1. Prerequisites
- **Python 3.10+**
- **FFmpeg** on system `PATH` (recommended for fastest encoding & native lossless codecs):
  - **Windows**: `winget install Gyan.FFmpeg` or download from [ffmpeg.org](https://ffmpeg.org/download.html)
  - **macOS**: `brew install ffmpeg`
  - **Linux**: `sudo apt install ffmpeg`

### 2. Install Python Dependencies
```bash
git clone https://github.com/Devesh0007/FramED.git
cd FramED
pip install -r requirements.txt
```

---

## 💻 CLI Usage

The command-line interface provides `encode` and `decode` workflows with automatic mode detection.

### Encoding Files

```bash
# 1. Standard 4K Archival Mode (maximum density, lossless)
python main.py encode dataset.tar output_archive.avi

# 2. Platform-Resilient Mode (for uploading to YouTube / streaming platforms)
python main.py encode archive.zip youtube_ready.avi --mode youtube

# 3. Optical Mode (for screen capture or projector playback)
python main.py encode document.pdf optical_test.avi --mode optical

# 4. Encrypted Encoding (AES-256-GCM with passphrase)
python main.py encode secret_keys.kdbx vault.avi --password "my-super-secure-passphrase"
```

### Decoding Videos

```bash
# 1. Decode video (mode is automatically detected from the embedded manifest frame)
python main.py decode output_archive.avi ./recovered/

# 2. Decode an encrypted video
python main.py decode vault.avi ./recovered/ --password "my-super-secure-passphrase"

# 3. Force a specific decode mode (optional override)
python main.py decode youtube_ready.avi ./recovered/ --mode youtube
```

---

## 🛡️ Error Correction & Security

FramED incorporates multi-tiered reliability and defense mechanisms:

1. **Cross-Frame XOR Parity Groups**:
   - Frames are grouped into batches ($G=8$ for `archive`, $G=3$ for `optical` and `youtube`).
   - Every group is followed by a computed XOR parity frame.
   - If any single frame in a group is dropped, truncated, or fails CRC32 validation, the decoder algebraically reconstructs the missing payload on the fly.
2. **Per-Frame CRC32 Integrity**:
   - Every frame embeds a 32-bit CRC checksum computed over its raw payload. Corrupted frames are instantly detected and marked for parity recovery.
3. **Enterprise-Grade Cryptography**:
   - Key derivation using **PBKDF2-HMAC-SHA256** with **100,000 iterations** and a cryptographically secure 32-byte salt.
   - Payload encryption using **AES-256 in Galois/Counter Mode (GCM)** with a 16-byte random nonce and 16-byte authentication tag.
   - Any bit tampering or incorrect passphrase immediately aborts decoding before corrupted data touches disk.

---

## 📐 Frame Architecture & Wire Protocol

Each frame consists of an outer synchronization border and an inner data grid:

```
┌────────────────────────────────────────────────────────────────────────┐
│  SYNC BORDER (alternating checkerboard pattern, N-cells wide)          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  FRAME HEADER (39 bytes, big-endian)                             │  │
│  │  MAGIC(4) VERSION(1) TYPE(1) FRAME_ID(4) TOTAL_FRAMES(4)        │  │
│  │  FILE_ID(16) CHUNK_ID(4) PAYLOAD_LEN(4) FLAGS(1)                │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │  PAYLOAD BYTES (variable length, up to mode capacity)            │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │  CRC32 CHECKSUM (4 bytes of raw payload)                         │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │  PADDING CELLS (neutral gray 128 fill for remaining inner cells) │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

### 39-Byte Header Specification (`!4sBBII16sIIB`)

| Offset | Field | Type | Size | Description |
|---|---|---|---|---|
| `0x00` | `MAGIC` | `bytes[4]` | 4 B | Protocol identifier (`b'DV01'`) |
| `0x04` | `VERSION` | `uint8` | 1 B | Protocol version (`1`) |
| `0x05` | `TYPE` | `uint8` | 1 B | `0x00` = MANIFEST, `0x01` = DATA, `0x02` = PARITY |
| `0x06` | `FRAME_ID` | `uint32` | 4 B | Monotonic sequential index across the entire video |
| `0x0A` | `TOTAL_FRAMES`| `uint32` | 4 B | Total frame count in the video sequence |
| `0x0E` | `FILE_ID` | `bytes[16]`| 16 B| Unique UUID4 identifying the payload transmission |
| `0x1E` | `CHUNK_ID` | `uint32` | 4 B | Data chunk index (or group start chunk index for Parity) |
| `0x22` | `PAYLOAD_LEN` | `uint32` | 4 B | Exact pre-ECC payload byte length in this frame |
| `0x26` | `FLAGS` | `uint8` | 1 B | Feature flags (reserved for future protocol extensions) |
| **Total** | | | **39 B**| Fixed overhead before data payload |

---

## 📂 Project Structure

```
FramED/
├── framed/                      # Core FramED engine package
│   ├── __init__.py              # Package entry point
│   ├── config.py                # Protocol constants, ModeConfig, and mode presets
│   ├── pipeline.py              # High-level orchestration (encode_file / decode_file)
│   ├── utils.py                 # Bit/byte conversion, CRC32, UUID generation
│   ├── encoder/                 # Encoding pipeline components
│   │   ├── compressor.py        # Zstandard (zstd) compression & metadata header
│   │   ├── encryptor.py         # PBKDF2 + AES-256-GCM encryption
│   │   ├── chunker.py           # Mode-aware stream splitter
│   │   ├── fec.py               # Vectorized XOR parity & Reed-Solomon engine
│   │   ├── frame_builder.py     # Binary blob assembler (manifest, data, parity)
│   │   ├── renderer.py          # Array/PIL rasterizer with checkerboard borders
│   │   └── video_writer.py      # FFmpeg rawvideo pipe & OpenCV fallback muxer
│   └── decoder/                 # Decoding pipeline components
│       ├── video_reader.py      # OpenCV VideoCapture generator
│       ├── frame_parser.py      # Resampling, center-cell sampling & header parser
│       ├── fec_reconstructor.py # Multi-group XOR parity recovery engine
│       ├── reassembler.py       # Chunk sequencing & exact byte truncation
│       ├── decryptor.py         # Authenticated AES-GCM decryption
│       ├── decompressor.py      # Zstandard decompression & filename restoration
│       └── writer.py            # Clean filesystem writer
├── tests/                       # Automated test suite
│   ├── test_cell_rendering.py   # Pixel-accurate render & sampling unit tests
│   ├── test_compression.py      # Zstd compression/decompression identity tests
│   ├── test_fec.py              # XOR parity & Reed-Solomon recovery tests
│   └── test_roundtrip.py        # End-to-end encode → video → decode tests
├── main.py                      # Click CLI interface
├── requirements.txt             # Python package dependencies
├── Implementation.md            # In-depth architectural & optimization guide
└── README.md                    # Project documentation & quickstart
```

---

## 🧪 Testing

Run the full pytest suite:

```bash
pytest tests/ -v
```

> **Note**: Video round-trip tests will automatically detect FFmpeg and OpenCV availability.

---

## ⚠️ Critical Notes & Best Practices

1. **Lossless Archival**: Always use the `.avi` container generated by FramED with `archive` mode. Re-encoding `archive` mode videos using lossy H.264/H.265 compression will corrupt pixel values.
2. **Platform Sharing**: For uploading to YouTube or video hosts, **always select `--mode youtube`**. This activates 1-bit high-contrast cells and lossy-resilient encoding.
3. **Encryption Security**: Passphrases are not stored anywhere in the video. If you encrypt a file and lose the password, **your data is mathematically impossible to recover**.
