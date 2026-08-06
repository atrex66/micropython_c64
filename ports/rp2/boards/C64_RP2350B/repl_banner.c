// Classic Commodore 64 BASIC-style REPL startup banner, showing free heap
// RAM and free flash filesystem space in place of the default MicroPython
// version/board banner. See MICROPY_BOARD_FRIENDLY_REPL_BANNER in
// py/mpconfig.h / shared/runtime/pyexec.c.

#include "py/mphal.h"
#include "py/gc.h"
#include "py/nlr.h"
#include "py/obj.h"
#include "py/objtuple.h"
#include "extmod/vfs.h"

// Free bytes on the mounted "/" filesystem (statvfs f_frsize * f_bavail),
// or false if no filesystem is mounted there.
static bool c64_flash_bytes_free(size_t *out_bytes) {
    nlr_buf_t nlr;
    if (nlr_push(&nlr) == 0) {
        mp_obj_t root = mp_obj_new_str("/", 1);
        mp_obj_t statvfs_tuple = mp_vfs_statvfs(root);
        size_t len;
        mp_obj_t *items;
        mp_obj_tuple_get(statvfs_tuple, &len, &items);
        mp_int_t f_frsize = mp_obj_get_int(items[1]);
        mp_int_t f_bavail = mp_obj_get_int(items[4]);
        *out_bytes = (size_t)(f_frsize * f_bavail);
        nlr_pop();
        return true;
    } else {
        // No filesystem mounted at "/" (or statvfs failed); omit the line.
        return false;
    }
}

int c64_friendly_repl_banner(void) {
    mp_hal_stdout_tx_str("\033[2J\033[H"); // clear screen and home cursor
    mp_hal_stdout_tx_str("    **** C64 MICROPYTHON V0.1 ****\r\n");

    // Collect garbage first: by this point _boot.py/boot.py/main.py have
    // already run (vfs mount, module imports, etc.), leaving unreferenced
    // allocations that gc_info() would otherwise still count as "used",
    // understating the real free RAM until the user runs gc.collect().
    gc_collect();

    gc_info_t gc_info_obj;
    gc_info(&gc_info_obj);
    mp_printf(&mp_plat_print, "  520KB RAM SYSTEM %u BYTES FREE\r\n", (unsigned int)gc_info_obj.free);
    mp_printf(&mp_plat_print, "   C64 RAM SYSTEM 65535 BYTES FREE\r\n");

    size_t flash_free;
    if (c64_flash_bytes_free(&flash_free)) {
        mp_printf(&mp_plat_print, "   1024KB FLASH SYSTEM %u KB FREE\r\n", (unsigned int)flash_free / 1024);
    }

    mp_hal_stdout_tx_str("READY.\r\n");
    return 1;
}
