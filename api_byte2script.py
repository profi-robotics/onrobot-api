#!/usr/bin/env python3

from __future__ import annotations

import base64
from pathlib import Path
import zlib


def convert(data: str, output_path: Path | None = None) -> Path:
    decoded64 = base64.b64decode(data)
    final = zlib.decompress(decoded64)
    output = output_path or Path("legacy/api_original.py")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(final.decode("utf-8"), encoding="utf-8")
    print(f"Conversion completed: {output}")
    return output


if __name__ == "__main__":
    source = Path("api_byte.txt")
    data = source.read_text(encoding="utf-8")
    convert(data)
