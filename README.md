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

MicroPython runs on a wide range of microcontrollers, as well as on Unix-like
(including Linux, BSD, macOS, WSL) and Windows systems.

Microcontroller targets can be as small as 256kiB flash + 16kiB RAM, although
devices with at least 512kiB flash + 128kiB RAM allow a much more
full-featured experience.

The [Unix](ports/unix) and [Windows](ports/windows) ports allow both
development and testing of MicroPython itself, as well as providing
lightweight alternative to CPython on these platforms (in particular on
embedded Linux systems).

Over twenty different MicroPython ports are provided in this repository,
split across three
[MicroPython Support Tiers](https://docs.micropython.org/en/latest/develop/support_tiers.html).

Tier 1 Ports
============

👑 Ports in [Tier 1](https://docs.micropython.org/en/latest/develop/support_tiers.html)
are mature and have the most active development, support and testing:

| Port                     | Target                                                                                 | Quick Reference                                                      |
|--------------------------|----------------------------------------------------------------------------------------|----------------------------------------------------------------------|
| [esp32](ports/esp32)*    | Espressif ESP32 SoCs (ESP32, ESP32S2, ESP32S3, ESP32C3, ESP32C6)                       | [here](https://docs.micropython.org/en/latest/esp32/quickref.html)   |
| [mimxrt](ports/mimxrt)   | NXP m.iMX RT                                                                           | [here](https://docs.micropython.org/en/latest/mimxrt/quickref.html)  |
| [rp2](ports/rp2)         | Raspberry Pi RP2040 and RP2350                                                         | [here](https://docs.micropython.org/en/latest/rp2/quickref.html)     |
| [samd](ports/samd)       | Microchip (formerly Atmel) SAMD21 and SAMD51                                           | [here](https://docs.micropython.org/en/latest/samd/quickref.html)    |
| [stm32](ports/stm32)     | STMicroelectronics STM32 MCUs (F0, F4, F7, G0, G4, H5, H7, L0, L1, L4, N6, WB, WL)     | [here](https://docs.micropython.org/en/latest/pyboard/quickref.html) |
| [unix](ports/unix)       | Linux, BSD, macOS, WSL                                                                 | [here](https://docs.micropython.org/en/latest/unix/quickref.html)    |
| [windows](ports/windows) | Microsoft Windows                                                                      | [here](https://docs.micropython.org/en/latest/unix/quickref.html)    |

An asterisk indicates that the port has ongoing financial support from the vendor.

Tier 2 Ports
============

✔ Ports in [Tier 2](https://docs.micropython.org/en/latest/develop/support_tiers.html)
are less mature and less actively developed and tested than Tier 1, but
still fully supported:

| Port                             | Target                                                      | Quick Reference                                                         |
|----------------------------------|-------------------------------------------------------------|-------------------------------------------------------------------------|
| [alif](ports/alif)               | Alif Semiconductor Ensemble MCUs (E3, E7)                   |                                                                         |
| [embed](ports/embed)             | Generates a set of .c/.h files for embedding into a project |                                                                         |
| [nrf](ports/nrf)                 | Nordic Semiconductor nRF51 and nRF52                        |                                                                         |
| [psoc-edge](ports/psoc-edge)     | Infineon PSOC™ Edge                                         | [here](https://docs.micropython.org/en/latest/psoc-edge/quickref.html)  |
| [renesas-ra](ports/renesas-ra)   | Renesas RA family                                           | [here](https://docs.micropython.org/en/latest/renesas-ra/quickref.html) |
| [webassembly](ports/webassembly) | Emscripten port targeting browsers and NodeJS               |                                                                         |
| [zephyr](ports/zephyr)           | Zephyr RTOS                                                 | [here](https://docs.micropython.org/en/latest/zephyr/quickref.html)     |

Tier 3 Ports
============

Ports in [Tier 3](https://docs.micropython.org/en/latest/develop/support_tiers.html)
are built in CI but not regularly tested by the MicroPython maintainers:

| Port                       | Target                                                            | Quick Reference                                                         |
|----------------------------|-------------------------------------------------------------------|-------------------------------------------------------------------------|
| [cc3200](ports/cc3200)     | Texas Instruments CC3200                                          | [For WiPy](https://docs.micropython.org/en/latest/wipy/quickref.html)   |
| [esp8266](ports/esp8266)   | Espressif ESP8266 SoC                                             | [here](https://docs.micropython.org/en/latest/esp8266/quickref.html)    |
| [pic16bit](ports/pic16bit) | Microchip PIC 16-bit                                              |                                                                         |

Additional Ports
================

In addition to the above there is a Tier M containing ports that are used
primarily for maintenance, development and testing:

- The ["bare-arm"](ports/bare-arm) port is an example of the absolute minimum
  configuration that still includes the compiler, and is used to keep track
  of the code size of the core runtime and VM.

- The ["minimal"](ports/minimal) port provides an example of a very basic
  MicroPython port and can be compiled as both a standalone Linux binary as
  well as for ARM Cortex-M4. Start with this if you want to port MicroPython
  to another microcontroller.

- The [qemu](ports/qemu) port is a QEMU-based emulated target for Cortex-A,
  Cortex-M, RISC-V 32-bit, RISC-V 64-bit, and PowerPC 64-bit architectures.

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
