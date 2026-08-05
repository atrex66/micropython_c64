#!/usr/bin/env bash
# Build C64 MicroPython Cartridge firmware WITHOUT PSRAM support.
#
# Use this if your cartridge PCB has no APS6404L PSRAM chip fitted.
# For a PSRAM-enabled build, use build_psram.sh instead.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/ports/rp2"

BUILD_DIR="build-C64_RP2350B"

cmake -S . -B "$BUILD_DIR" \
    -DPICO_BUILD_DOCS=0 \
    -DMICROPY_BOARD=C64_RP2350B \
    -DMICROPY_BOARD_DIR="$(pwd)/boards/C64_RP2350B" \
    -DCMAKE_BUILD_TYPE=Debug \
    -DPICOTOOL_FORCE_FETCH_FROM_GIT=1 \
    -DMICROPY_HW_ENABLE_PSRAM=0

make -C "$BUILD_DIR" -j"$(nproc)"

echo
echo "Firmware: ports/rp2/$BUILD_DIR/firmware.uf2"
