"""Throwaway CRILAYLA decoder probe for the local Storm 4 sample."""
from pathlib import Path
import struct
import sys


class Bits:
    def __init__(self, data: bytes):
        self.data = data[::-1]
        self.pos = 0

    def read(self, count: int) -> int:
        value = 0
        for _ in range(count):
            byte_index, bit_index = divmod(self.pos, 8)
            if byte_index >= len(self.data):
                raise EOFError("CRILAYLA bitstream ended early")
            value = (value << 1) | ((self.data[byte_index] >> (7 - bit_index)) & 1)
            self.pos += 1
        return value


def decompress(blob: bytes) -> bytes:
    if blob[:8] != b"CRILAYLA":
        raise ValueError("missing CRILAYLA marker")
    size, header_offset = struct.unpack_from("<II", blob, 8)
    if header_offset != 0:
        # The known CRILAYLA variant stores a 0x100-byte raw header at file end;
        # the field is the relative offset to that header.
        if header_offset + 0x10 + 0x100 > len(blob):
            raise ValueError(f"invalid raw-header offset {header_offset:#x}")
    if len(blob) < 0x110 or size > 128 * 1024 * 1024:
        raise ValueError("invalid CRILAYLA dimensions")
    raw_header = blob[-0x100:]
    comp = blob[0x10:-0x100]
    bits = Bits(comp)
    reverse_out = bytearray()
    while len(reverse_out) < size:
        if bits.read(1):
            offset = bits.read(13) + 3
            count = 3
            for width in (2, 3, 5, 8):
                part = bits.read(width)
                count += part
                if part != (1 << width) - 1:
                    break
            else:
                count += bits.read(8)
            if offset > len(reverse_out):
                raise ValueError(f"backreference {offset} exceeds output {len(reverse_out)}")
            for _ in range(count):
                reverse_out.append(reverse_out[-offset])
                if len(reverse_out) == size:
                    break
        else:
            reverse_out.append(bits.read(8))
    return raw_header + reverse_out[::-1]


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: decode_crilayla_probe.py input.xfbin output.xfbin")
    result = decompress(Path(sys.argv[1]).read_bytes())
    Path(sys.argv[2]).write_bytes(result)
    print(f"decoded {len(result):,} bytes; signature={result[:16].hex(' ')}")

