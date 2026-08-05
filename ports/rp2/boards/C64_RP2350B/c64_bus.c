// machine.C64Bus: PIO-driven Commodore 64 expansion-port address/data bus.
//
// See c64_cart_pinout.md (workspace root) for the full cartridge pin map.
// GP0 is reserved for PSRAM CS1; the bus itself starts at GP1.

#include "py/runtime.h"
#include "py/mphal.h"

#include "hardware/pio.h"
#include "hardware/gpio.h"

#include "address.pio.h"
#include "c64_bus.h"

// GPIO pin map (shifted +1 vs. the raw cartridge pinout to free GP0 for PSRAM CS1).
#define C64_ADDR_PIN_BASE (1)   // GP1..GP16:  A15..A0
#define C64_RW_PIN        (17)  // GP17: R/W cart, GP18: 245-DIR, GP19: addr OE, GP20: data OE
#define C64_DATA_PIN_BASE (21)  // GP21..GP28: D7..D0
#define C64_PHI2_PIN      (29)
#define C64_BA_PIN        (30)

// Range of GPIOs switched to PIO function-select by adressdata_program_init().
// Includes _Reset (GP31) and _IRQ (GP32), which aren't touched by the PIO
// program itself but are kept in-range to match the original driver's span.
#define CARTRIDGE_GPIO_FIRST (1)
#define CARTRIDGE_GPIO_LAST  (32)

// The cartridge wiring is MSB-first while PIO pin groups are LSB-first:
// GP1=A15 ... GP16=A0 and GP21=D7 ... GP28=D0.
static uint8_t reverse_bits8(uint8_t value) {
    value = (uint8_t)(((value & 0x55u) << 1) | ((value >> 1) & 0x55u));
    value = (uint8_t)(((value & 0x33u) << 2) | ((value >> 2) & 0x33u));
    return (uint8_t)((value << 4) | (value >> 4));
}

static uint16_t reverse_bits16(uint16_t value) {
    return (uint16_t)(((uint16_t)reverse_bits8((uint8_t)value) << 8) |
        reverse_bits8((uint8_t)(value >> 8)));
}

static uint32_t c64_pio_command(uint16_t address, bool read, uint8_t data) {
    // With left-shifting OUT instructions, consume address from [31:16],
    // R/W from [15], and write data from [14:7].
    return ((uint32_t)reverse_bits16(address) << 16) |
        ((uint32_t)read << 15) |
        ((uint32_t)reverse_bits8(data) << 7);
}

static void adressdata_program_init(PIO pio) {
    pio_set_gpio_base(pio, 0);
    for (int i = CARTRIDGE_GPIO_FIRST; i <= CARTRIDGE_GPIO_LAST; i++) { // address and data
        pio_gpio_init(pio, i);
    }

    uint offset = pio_add_program(pio, &c64cartridgeaddress_program);
    pio_sm_config c_addr = c64cartridgeaddress_program_get_default_config(offset);
    sm_config_set_out_pins(&c_addr, C64_ADDR_PIN_BASE, 16);
    sm_config_set_in_pins(&c_addr, C64_DATA_PIN_BASE);
    sm_config_set_in_pin_count(&c_addr, 8);
    sm_config_set_sideset_pins(&c_addr, C64_RW_PIN);
    sm_config_set_out_shift(&c_addr, false, false, 32);
    sm_config_set_in_shift(&c_addr, false, false, 32);
    pio_sm_init(pio, 0, offset, &c_addr);
    pio_sm_set_consecutive_pindirs(pio, 0, C64_ADDR_PIN_BASE, 16, true);
    pio_sm_set_consecutive_pindirs(pio, 0, C64_RW_PIN, 4, true);
    pio_sm_set_enabled(pio, 0, true);
}

static void c64_write_data(PIO pio, uint16_t address, uint8_t data) {
    pio_sm_put_blocking(pio, 0, c64_pio_command(address, false, data));
}

static void c64_read_data(PIO pio, uint16_t address, uint8_t *data) {
    pio_sm_put_blocking(pio, 0, c64_pio_command(address, true, 0));
    *data = reverse_bits8((uint8_t)pio_sm_get_blocking(pio, 0));
}

// Shared bus hardware state. This is deliberately global (not per-instance)
// so that the bare peek()/poke() builtins below and the machine.C64Bus class
// both talk to the same PIO/state machine, and so peek()/poke() work even
// before any machine.C64Bus object has been constructed -- e.g. for using
// the C64 as a REPL output device, the bus needs to come up before
// "import machine"/C64Bus is ever reached.
static PIO c64_bus_pio;
static bool c64_bus_hw_ready = false;

static void c64_bus_ensure_hw_init(void) {
    if (!c64_bus_hw_ready) {
        c64_bus_pio = pio0;
        adressdata_program_init(c64_bus_pio);
        c64_bus_hw_ready = true;
    }
}

// Bus-master initialization: bring up the C64 expansion bus signals
// (e.g. drive/release _Reset, BA, DMA, wait for PHI2) before the cartridge
// starts acting as bus master. Left empty for the KERNAL-style init sequence
// to be implemented here. Operates on the shared global bus state since it
// runs at boot (see c64_board_early_init()), before any machine.C64Bus
// Python object exists.
static void c64_init(void) {
}

// Called from MICROPY_BOARD_EARLY_INIT() (ports/rp2/main.c), before mp_init(),
// frozen boot scripts, and the first REPL banner print -- so the C64 side is
// ready to receive bytes before MicroPython ever writes anything.
void c64_board_early_init(void) {
    c64_bus_ensure_hw_init();
    c64_init();
}

typedef struct _machine_c64bus_obj_t {
    mp_obj_base_t base;
    PIO pio;
} machine_c64bus_obj_t;

static mp_obj_t machine_c64bus_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *args) {
    mp_arg_check_num(n_args, n_kw, 0, 0, false);
    machine_c64bus_obj_t *self = mp_obj_malloc(machine_c64bus_obj_t, type);
    c64_bus_ensure_hw_init();
    self->pio = c64_bus_pio;
    return MP_OBJ_FROM_PTR(self);
}

static mp_obj_t machine_c64bus_peek(mp_obj_t self_in, mp_obj_t addr_in) {
    machine_c64bus_obj_t *self = MP_OBJ_TO_PTR(self_in);
    uint8_t data;
    c64_read_data(self->pio, (uint16_t)mp_obj_get_int(addr_in), &data);
    return MP_OBJ_NEW_SMALL_INT(data);
}
static MP_DEFINE_CONST_FUN_OBJ_2(machine_c64bus_peek_obj, machine_c64bus_peek);

static mp_obj_t machine_c64bus_poke(mp_obj_t self_in, mp_obj_t addr_in, mp_obj_t data_in) {
    machine_c64bus_obj_t *self = MP_OBJ_TO_PTR(self_in);
    c64_write_data(self->pio, (uint16_t)mp_obj_get_int(addr_in), (uint8_t)mp_obj_get_int(data_in));
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_3(machine_c64bus_poke_obj, machine_c64bus_poke);

// Bare `peek`/`poke` builtins (not `static`: declared `extern` and wired into
// the `builtins` module via MICROPY_PORT_BUILTINS in mpconfigboard.h), so
// they're available everywhere without importing machine.C64Bus. Each call
// lazily brings up the bus hardware on first use via c64_bus_ensure_hw_init().
mp_obj_t mp_c64_peek(mp_obj_t addr_in) {
    c64_bus_ensure_hw_init();
    uint8_t data;
    c64_read_data(c64_bus_pio, (uint16_t)mp_obj_get_int(addr_in), &data);
    return MP_OBJ_NEW_SMALL_INT(data);
}
MP_DEFINE_CONST_FUN_OBJ_1(mp_c64_peek_obj, mp_c64_peek);

mp_obj_t mp_c64_poke(mp_obj_t addr_in, mp_obj_t data_in) {
    c64_bus_ensure_hw_init();
    c64_write_data(c64_bus_pio, (uint16_t)mp_obj_get_int(addr_in), (uint8_t)mp_obj_get_int(data_in));
    return mp_const_none;
}
MP_DEFINE_CONST_FUN_OBJ_2(mp_c64_poke_obj, mp_c64_poke);

static const mp_rom_map_elem_t machine_c64bus_locals_dict_table[] = {
    { MP_ROM_QSTR(MP_QSTR_peek), MP_ROM_PTR(&machine_c64bus_peek_obj) },
    { MP_ROM_QSTR(MP_QSTR_poke), MP_ROM_PTR(&machine_c64bus_poke_obj) },
};
static MP_DEFINE_CONST_DICT(machine_c64bus_locals_dict, machine_c64bus_locals_dict_table);

MP_DEFINE_CONST_OBJ_TYPE(
    c64_bus_type,
    MP_QSTR_C64Bus,
    MP_TYPE_FLAG_NONE,
    make_new, machine_c64bus_make_new,
    locals_dict, &machine_c64bus_locals_dict
    );
