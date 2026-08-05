// Declarations for the bare `peek`/`poke` builtins implemented in c64_bus.c.
//
// This is a separate header (rather than declaring these directly in
// mpconfigboard.h) because mpconfigboard.h is processed very early, from
// inside py/obj.h's own include of py/mpconfig.h -- before py/obj.h has
// defined MP_DECLARE_CONST_FUN_OBJ_1/2 or mp_obj_fun_builtin_fixed_t. This
// header is instead included later, via MICROPY_BOARD_BUILTINS_HEADER in
// py/modbuiltins.c, once py/obj.h is fully available.
#ifndef MICROPY_INCLUDED_C64_RP2350B_C64_BUS_H
#define MICROPY_INCLUDED_C64_RP2350B_C64_BUS_H

#include "py/obj.h"

MP_DECLARE_CONST_FUN_OBJ_1(mp_c64_peek_obj);
MP_DECLARE_CONST_FUN_OBJ_2(mp_c64_poke_obj);

// Boot-time C64 bus bring-up, called from MICROPY_BOARD_EARLY_INIT()
// (ports/rp2/main.c) before mp_init()/boot scripts/the first REPL banner.
void c64_board_early_init(void);

#endif
