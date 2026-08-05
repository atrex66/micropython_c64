// Board and hardware configuration for the C64 MicroPython Cartridge.
#define MICROPY_HW_BOARD_NAME                   "C64 MicroPython Cartridge"

// RP2354B0A4 flash capacity; this must match mpconfigboard.cmake.
#define PICO_FLASH_SIZE_BYTES                   (2 * 1024 * 1024)

// USB CDC remains enabled by the RP2 port default.  Add a FAT filesystem
// exported to the connected PC as a USB mass-storage device.
#define MICROPY_HW_USB_MSC                      (1)
#define MICROPY_HW_USB_MSC_INQUIRY_VENDOR_STRING "C64Micro"
#define MICROPY_HW_USB_MSC_INQUIRY_PRODUCT_STRING "MicroPython Disk"
#define MICROPY_HW_USB_MSC_INQUIRY_REVISION_STRING "1.00"

// GP0 is a dedicated PSRAM CS1 pin (not user-selectable).  GP1-GP39 are
// connected to C64 bus drivers and must not be selected as default
// peripheral pins.  GP40-GP47 are available to user code.
#define MICROPY_HW_I2C_NO_DEFAULT_PINS          (1)
#define MICROPY_HW_SPI_NO_DEFAULT_PINS          (1)
#define MICROPY_HW_UART_NO_DEFAULT_PINS          (1)

// Expose machine.C64Bus, the PIO-driven C64 expansion-port bus driver.
#define MICROPY_PY_MACHINE_C64BUS               (1)

// Bare `peek`/`poke` builtins (see c64_bus.c/c64_bus.h), available globally
// without importing machine.C64Bus first -- e.g. so the C64 bus can be
// brought up before it's used as a REPL output device. They lazily init the
// bus hardware on first use. The declarations live in c64_bus.h, pulled in
// by py/modbuiltins.c via MICROPY_BOARD_BUILTINS_HEADER (see there for why).
#define MICROPY_BOARD_BUILTINS_HEADER "c64_bus.h"
#define MICROPY_PORT_BUILTINS \
    { MP_ROM_QSTR(MP_QSTR_peek), MP_ROM_PTR(&mp_c64_peek_obj) }, \
    { MP_ROM_QSTR(MP_QSTR_poke), MP_ROM_PTR(&mp_c64_poke_obj) },

// Classic Commodore 64 BASIC-style REPL banner (see repl_banner.c), showing
// free RAM/flash instead of the default MicroPython version/board banner.
int c64_friendly_repl_banner(void);
#define MICROPY_BOARD_FRIENDLY_REPL_BANNER()    c64_friendly_repl_banner()

// Bring up the C64 expansion bus (PIO/GPIO) and run the KERNAL-style
// bus-master init before MicroPython prints anything (boot scripts, REPL
// banner) -- see c64_bus.c c64_board_early_init()/c64_init().
void c64_board_early_init(void);
#define MICROPY_BOARD_EARLY_INIT()              c64_board_early_init()