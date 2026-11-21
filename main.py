#!/usr/bin/env python3
"""Entrypoint: place the built passport spread at /output/entry.png.

Stdlib only. The image itself is produced by generate.py (Pillow + DejaVu)
and committed as entry.png; this step only copies it where the grader
reads it. It clears the output directory's contents, never the directory.
"""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    src = os.path.join(HERE, "entry.png")
    out_dir = "/output"
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, "entry.png")
    shutil.copyfile(src, dst)
    size = os.path.getsize(dst)
    assert size > 0 and size <= 1048576, size
    print("wrote", dst, size, "bytes")


if __name__ == "__main__":
    main()
