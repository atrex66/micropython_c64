/*
 * Local pico-sdk board definition for the C64 MicroPython Cartridge.
 * This file may be included by assembler sources, so keep it to preprocessor
 * definitions only.
 */
#ifndef _BOARDS_C64_RP2350B_H
#define _BOARDS_C64_RP2350B_H

// RP2354B0A4 is an RP2350B-family QFN-80 package with 48 GPIOs.
#define PICO_RP2350A 0

// The selected boot stage supports the cartridge flash interface.
#define PICO_BOOT_STAGE2_CHOOSE_W25Q080 1

#endif