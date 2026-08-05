# C64_RP2350B board

RP2354B0A4 (RP2350B family, QFN-80, 48 GPIO) based Commodore 64 cartridge,
with 2MiB of internal flash and an optional fitted APS6404L QSPI PSRAM chip.

See `c64_cart_pinout.md` (workspace root) for the full cartridge pin map.

## PSRAM

The board enables `MICROPY_HW_ENABLE_PSRAM` by default, with the PSRAM
chip-select wired to GP0. The C64 expansion bus signals are shifted up by
one GPIO (A15 on GP1 ... `_Freeze` on GP39) to keep GP0 free and
GPIO-routable as QMI CS1.

If your cartridge PCB has no PSRAM fitted, disable it at configure time:

```bash
cd ports/rp2
cmake -S . -B build-C64_RP2350B \
  -DPICO_BUILD_DOCS=0 \
  -DMICROPY_BOARD=C64_RP2350B \
  -DMICROPY_BOARD_DIR="$(pwd)/boards/C64_RP2350B" \
  -DCMAKE_BUILD_TYPE=Debug \
  -DPICOTOOL_FORCE_FETCH_FROM_GIT=1 \
  -DMICROPY_HW_ENABLE_PSRAM=0
make -C build-C64_RP2350B -j"$(nproc)"
```

`MICROPY_HW_ENABLE_PSRAM` is only set to `1` in `mpconfigboard.cmake` when
not already defined, so the `-D` override above takes precedence over the
board default without needing any source changes.

## machine.C64Bus

`c64_bus.c` implements `machine.C64Bus`, a PIO-driven driver for the C64
expansion-port address/data bus (see `address.pio`). It is enabled via the
`MICROPY_PY_MACHINE_C64BUS` build option (on by default for this board) and
registered into the `machine` module in `modmachine.c`.

### Python usage

```python
from machine import C64Bus

bus = C64Bus()                # no constructor arguments; claims PIO0 SM0

value = bus.peek(0xD000)      # int, 0-255
bus.poke(0xD000, 0x42)        # returns None
```

- `C64Bus()` takes no arguments.
- `peek(addr)` — `addr` is a 16-bit address (0-65535); returns the byte
  read as an int (0-255).
- `poke(addr, data)` — `addr` is a 16-bit address, `data` is an 8-bit
  value (0-255); returns `None`.

### Known limitations

- There is no `deinit()` method; once constructed, the `C64Bus` instance
  keeps PIO0 state machine 0 claimed for its lifetime.
- Only one `C64Bus` instance should be created at a time. A second instance
  would silently reinitialize the same PIO0/SM0 program slot rather than
  raising an error.

## REPL startup banner

The friendly REPL's startup banner (`repl_banner.c`) is replaced with a
classic Commodore 64 BASIC-style message showing free heap RAM and free
flash filesystem space instead of the usual MicroPython version/board line:

```
**** C64 MICROPYTHON CARTRIDGE ****
 123456 BYTES RAM FREE
 654321 BYTES FLASH FREE
READY.
>>>
```

RAM free comes from the GC heap (`gc.mem_free()`-equivalent); flash free
comes from `os.statvfs('/')` on the mounted flash filesystem (the line is
omitted if nothing is mounted at `/`). This is wired in via the
`MICROPY_BOARD_FRIENDLY_REPL_BANNER()` hook (defined in
`py/mpconfig.h`/`shared/runtime/pyexec.c`), which any board can override to
fully replace the default banner.
