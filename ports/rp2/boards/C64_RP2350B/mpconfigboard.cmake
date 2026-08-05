# CMake configuration for the C64 MicroPython Cartridge.
#
# This is an RP2354B0A4 (RP2350B family, QFN-80, 48 GPIO) cartridge board
# with 2MiB of internal flash.

set(PICO_NUM_GPIOS 48)

# This is a local pico-sdk board definition, not one supplied by pico-sdk.
list(APPEND PICO_BOARD_HEADER_DIRS ${MICROPY_BOARD_DIR})
set(PICO_BOARD "c64_rp2350b")
set(PICO_PLATFORM "rp2350")
set(PICO_FLASH_SIZE_BYTES 2097152)

# Reserve 1MiB for firmware and expose the remaining 1MiB as the FAT
# filesystem exported over USB mass storage.
if(NOT DEFINED MICROPY_HW_FLASH_STORAGE_BYTES)
    set(MICROPY_HW_FLASH_STORAGE_BYTES 1048576)
endif()

# The fitted APS6404L PSRAM chip-select is wired to GP0.  The C64 bus signals
# are shifted up by one GPIO (A15 on GP1 ... _Freeze on GP39) to make GP0
# available as a dedicated, GPIO-routable QMI CS1 pin for the stock pico-sdk
# hardware_psram driver; see c64_cart_pinout.md for the full pin map.
if(NOT DEFINED MICROPY_HW_ENABLE_PSRAM)
    set(MICROPY_HW_ENABLE_PSRAM 1)
endif()
if(NOT DEFINED MICROPY_HW_PSRAM_CS_PIN)
    set(MICROPY_HW_PSRAM_CS_PIN 0)
endif()

set(MICROPY_FROZEN_MANIFEST ${MICROPY_BOARD_DIR}/manifest.py)

# machine.C64Bus: PIO-driven C64 expansion-port address/data bus.
list(APPEND MICROPY_BOARD_PIO_FILES ${MICROPY_BOARD_DIR}/address.pio)
list(APPEND MICROPY_SOURCE_BOARD ${MICROPY_BOARD_DIR}/c64_bus.c)

# Classic C64 BASIC-style REPL startup banner.
list(APPEND MICROPY_SOURCE_BOARD ${MICROPY_BOARD_DIR}/repl_banner.c)