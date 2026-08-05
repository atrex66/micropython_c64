#!/usr/bin/env bash
# Build C64 MicroPython Cartridge firmware WITH PSRAM support.
#
# Use this if your cartridge PCB has the APS6404L PSRAM chip fitted
# (chip-select wired to GP0). For a cart without PSRAM, use build.sh instead.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/ports/rp2"

BUILD_DIR="build-C64_RP2350B-PSRAM"

cmake -S . -B "$BUILD_DIR" \
    -DPICO_BUILD_DOCS=0 \
    -DMICROPY_BOARD=C64_RP2350B \
    -DMICROPY_BOARD_DIR="$(pwd)/boards/C64_RP2350B" \
    -DCMAKE_BUILD_TYPE=Debug \
    -DPICOTOOL_FORCE_FETCH_FROM_GIT=1 \
    -DMICROPY_HW_ENABLE_PSRAM=1

make -C "$BUILD_DIR" -j"$(nproc)"

echo
echo "Firmware: ports/rp2/$BUILD_DIR/firmware.uf2"
