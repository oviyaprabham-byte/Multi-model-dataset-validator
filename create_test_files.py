"""
Generate test audio and image files for the Dataset Validator.
Run this from the project root to create all test assets.
"""
import struct
import math
import os
import zipfile
from pathlib import Path

# ── WAV helpers ────────────────────────────────────────────────────────────

def make_wav(filename, duration_s=2.0, sample_rate=22050, frequency=440.0, volume=0.5, silent=False):
    """Write a minimal valid PCM WAV file."""
    num_channels = 1
    bits_per_sample = 16
    num_samples = int(sample_rate * duration_s)
    data_size = num_samples * num_channels * (bits_per_sample // 8)

    samples = []
    for i in range(num_samples):
        if silent:
            v = 0
        else:
            v = int(volume * 32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
        samples.append(max(-32768, min(32767, v)))

    with open(filename, "wb") as f:
        # RIFF header
        f.write(b"RIFF")
        f.write(struct.pack("<I", 36 + data_size))
        f.write(b"WAVE")
        # fmt chunk
        f.write(b"fmt ")
        f.write(struct.pack("<I", 16))          # chunk size
        f.write(struct.pack("<H", 1))           # PCM
        f.write(struct.pack("<H", num_channels))
        f.write(struct.pack("<I", sample_rate))
        f.write(struct.pack("<I", sample_rate * num_channels * (bits_per_sample // 8)))
        f.write(struct.pack("<H", num_channels * (bits_per_sample // 8)))
        f.write(struct.pack("<H", bits_per_sample))
        # data chunk
        f.write(b"data")
        f.write(struct.pack("<I", data_size))
        f.write(struct.pack(f"<{num_samples}h", *samples))

# ── PNG helpers ────────────────────────────────────────────────────────────

import zlib

def make_png(filename, width=64, height=64, r=100, g=150, b=200):
    """Write a minimal valid PNG file."""
    def png_chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack(">I", len(data)) + c + crc

    # Build raw image data (RGB)
    raw_rows = []
    for y in range(height):
        row = b'\x00'  # filter type = None
        for x in range(width):
            row += bytes([r, g, b])
        raw_rows.append(row)

    raw_data = b''.join(raw_rows)
    compressed = zlib.compress(raw_data)

    # IHDR
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    # Chunks
    ihdr = png_chunk(b"IHDR", ihdr_data)
    idat = png_chunk(b"IDAT", compressed)
    iend = png_chunk(b"IEND", b"")

    with open(filename, "wb") as f:
        f.write(b'\x89PNG\r\n\x1a\n')  # PNG signature
        f.write(ihdr)
        f.write(idat)
        f.write(iend)


# ── Build "clean" audio ZIP (READY) ───────────────────────────────────────
print("Creating test_audio_clean.zip (READY — 3 clean WAV files, consistent SR)...")
os.makedirs("_tmp_audio_clean", exist_ok=True)
for i, freq in enumerate([440, 880, 660]):
    make_wav(f"_tmp_audio_clean/clip_{i+1}.wav", duration_s=2.0, frequency=freq)

with zipfile.ZipFile("test_audio_clean.zip", "w") as z:
    for p in Path("_tmp_audio_clean").glob("*.wav"):
        z.write(str(p), p.name)

import shutil; shutil.rmtree("_tmp_audio_clean")
print("  -> test_audio_clean.zip created.")

# ── Build "messy" audio ZIP (NOT READY) ───────────────────────────────────
print("Creating test_audio_messy.zip (NOT READY — corrupted + silent WAV files)...")
os.makedirs("_tmp_audio_messy", exist_ok=True)

# 1 good file
make_wav("_tmp_audio_messy/good.wav", duration_s=2.0, frequency=440)
# 1 silent file
make_wav("_tmp_audio_messy/silent.wav", duration_s=1.0, silent=True)
# 1 corrupted file (random garbage bytes)
with open("_tmp_audio_messy/corrupted.wav", "wb") as f:
    f.write(b"RIFF\x00\x00\x00\x00WAVEfmt \xff\xfe\xfd\xfc" + b"\x00" * 50)

with zipfile.ZipFile("test_audio_messy.zip", "w") as z:
    for p in Path("_tmp_audio_messy").iterdir():
        z.write(str(p), p.name)

shutil.rmtree("_tmp_audio_messy")
print("  -> test_audio_messy.zip created.")

# ── Build "clean" image ZIP (READY) ───────────────────────────────────────
print("Creating test_image_clean.zip (READY — 6 unique PNGs in 2 balanced class folders)...")
os.makedirs("_tmp_img_clean/cats", exist_ok=True)
os.makedirs("_tmp_img_clean/dogs", exist_ok=True)

# Use a unique gradient per image so perceptual hashes differ
def make_unique_png(filename, width=64, height=64, seed=0):
    """Write a unique gradient PNG so phash doesn't flag as duplicate."""
    import random
    rng = random.Random(seed)
    r_base, g_base, b_base = rng.randint(50,255), rng.randint(50,255), rng.randint(50,255)
    raw_rows = []
    for y in range(height):
        row = b'\x00'
        for x in range(width):
            # Gradient that varies meaningfully per seed
            rv = (r_base + x * 3 + y * 2 + seed * 17) % 256
            gv = (g_base + x * 5 + y * 7 + seed * 31) % 256
            bv = (b_base + x * 7 + y * 3 + seed * 53) % 256
            row += bytes([rv, gv, bv])
        raw_rows.append(row)
    raw_data = b''.join(raw_rows)
    compressed = zlib.compress(raw_data)
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    def png_chunk(t, d):
        c = t + d; crc = struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack(">I", len(d)) + c + crc
    ihdr = png_chunk(b"IHDR", ihdr_data)
    idat = png_chunk(b"IDAT", compressed)
    iend = png_chunk(b"IEND", b"")
    with open(filename, "wb") as f:
        f.write(b'\x89PNG\r\n\x1a\n'); f.write(ihdr); f.write(idat); f.write(iend)

for i in range(3):
    make_unique_png(f"_tmp_img_clean/cats/cat_{i+1}.png", seed=i * 10 + 1)
    make_unique_png(f"_tmp_img_clean/dogs/dog_{i+1}.png", seed=i * 10 + 100)

with zipfile.ZipFile("test_image_clean.zip", "w") as z:
    for p in Path("_tmp_img_clean").rglob("*"):
        if p.is_file():
            z.write(str(p), str(p.relative_to("_tmp_img_clean")))

shutil.rmtree("_tmp_img_clean")
print("  -> test_image_clean.zip created.")

# ── Build "messy" image ZIP (NOT READY) ───────────────────────────────────
print("Creating test_image_messy.zip (NOT READY — corrupted + duplicate + imbalanced classes)...")
os.makedirs("_tmp_img_messy/cats", exist_ok=True)
os.makedirs("_tmp_img_messy/dogs", exist_ok=True)

# cats: 1 real image + 1 duplicate + 1 corrupted  → HIGH severity corrupted
for i in range(2):
    make_png(f"_tmp_img_messy/cats/cat_{i+1}.png", r=200, g=100, b=100)  # identical → duplicate
with open("_tmp_img_messy/cats/bad.png", "wb") as f:
    f.write(b"NOT_A_REAL_PNG_FILE\xff\xfe")

# dogs: only 1 image → severe class imbalance (3:1)
make_png("_tmp_img_messy/dogs/dog_1.png", r=100, g=100, b=200)

with zipfile.ZipFile("test_image_messy.zip", "w") as z:
    for p in Path("_tmp_img_messy").rglob("*"):
        if p.is_file():
            z.write(str(p), str(p.relative_to("_tmp_img_messy")))

shutil.rmtree("_tmp_img_messy")
print("  -> test_image_messy.zip created.")

print("\nAll test files created successfully!")
print("  test_audio_clean.zip — READY (clean WAVs, consistent SR)")
print("  test_audio_messy.zip — NOT READY (corrupted + silent WAVs)")
print("  test_image_clean.zip — READY (clean PNGs, balanced classes)")
print("  test_image_messy.zip — NOT READY (corrupted + duplicate + imbalanced)")
