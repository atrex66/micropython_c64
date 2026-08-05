# C64 MicroPython Cartridge

A MicroPython firmware for a custom RP2350B-based Commodore 64 expansion
cartridge. The RP2350B acts as the C64 bus master, driving the expansion
port's address/data bus, R/W, and control lines via PIO, with the goal of
running MicroPython as the C64's interactive environment — including
routing the REPL to the C64's 40x25 text screen and reading input from the
C64 keyboard.

Board: `C64_RP2350B` (RP2354B0A4, RP2350B family, 2 MiB flash, optional
APS6404L PSRAM).

## Building

Two build variants are provided, depending on whether your cartridge PCB has
the PSRAM chip fitted.

### Without PSRAM

```bash
./build.sh
```

Builds into `ports/rp2/build-C64_RP2350B/firmware.uf2`.

### With PSRAM

```bash
./build_psram.sh
```

Builds into `ports/rp2/build-C64_RP2350B-PSRAM/firmware.uf2`.

Both scripts wrap the equivalent manual `cmake`/`make` invocation with
`-DMICROPY_HW_ENABLE_PSRAM=1` or `=0`; flash the resulting `firmware.uf2` to
the board in BOOTSEL mode.


About this repository
---------------------

This repository contains the following components:
- [py/](py/) -- the core Python implementation, including compiler, runtime, and
  core library.
- [mpy-cross/](mpy-cross/) -- the MicroPython cross-compiler which is used to turn scripts
  into precompiled bytecode.
- [ports/](ports/) -- platform-specific code for the various ports and architectures that MicroPython runs on.
- [lib/](lib/) -- submodules for external dependencies.
- [tests/](tests/) -- test framework and test scripts.
- [docs/](docs/) -- user documentation in Sphinx reStructuredText format. This is used to generate the [online documentation](http://docs.micropython.org).
- [extmod/](extmod/) -- additional (non-core) modules implemented in C.
- [tools/](tools/) -- various tools, including the pyboard.py module.
- [examples/](examples/) -- a few example Python scripts.

"make" is used to build the components, or "gmake" on BSD-based systems.
You will also need bash, gcc, and Python 3.3+ available as the command `python3`.
Some ports (rp2 and esp32) additionally use CMake.

Supported platforms & architectures
-----------------------------------

This fork is only for the C64 mycropython cartridge


The MicroPython cross-compiler, mpy-cross
-----------------------------------------

Most ports require the [MicroPython cross-compiler](mpy-cross) to be built
first.  This program, called mpy-cross, is used to pre-compile Python scripts
to .mpy files which can then be included (frozen) into the
firmware/executable for a port.  To build mpy-cross use:

    $ cd mpy-cross
    $ make

External dependencies
---------------------

The core MicroPython VM and runtime has no external dependencies, but a given
port might depend on third-party drivers or vendor HALs. This repository
includes [several submodules](lib/) linking to these external dependencies.
Before compiling a given port, use

    $ cd ports/name
    $ make submodules

to ensure that all required submodules are initialised.
