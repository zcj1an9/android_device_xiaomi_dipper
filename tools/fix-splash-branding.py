#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Apply the dipper splash customization to the exact pinned GUI2 core.

No sleeping or initialization delays: retain the splash until four seconds
have elapsed before the normal home transition. Interactive startup prompts
keep their upstream routing. The upstream version and device labels remain.
"""
import hashlib
import sys
from pathlib import Path

PATCHES = [
    (
        'gui2/gui2.cpp',
        'd11a8063c695bbff59693040be5400db30b1669a9e74dde440cfa6e6e4713be5',
        '7845f04b1fad5a58427e9ccf28f9f416aa855c15b3df770f05183d761dacd2ae',
        '  if (splash_dismiss_pending && gui2_shell::splash_intro_finished()) {',
        '  // Keep the version and maintainer readable on fast normal boots. Startup\n  // continues in parallel; slow boots do not receive an extra four-second wait.\n  if (splash_dismiss_pending && gui2_shell::splash_intro_finished() &&\n      now_ms - splash_started_ms >= 4000) {',
    ),
    (
        'gui2/shell/splash.cpp',
        '49366cb3b9e495711e15e0cf40e707961395a27ed614066134f5d1c2a677f838',
        '8afe01c244fec81c7f317429f9bd0b64377bbd99751c1baa8e2b01b278eb7637',
        '  return view;\n}\n\nbool splash_intro_finished() {',
        '  lv_obj_t* maintainer = create_label(view.root, options.text_font, 0xE6E6EB, "ZC_J1an9");\n  lv_obj_align(maintainer, LV_ALIGN_BOTTOM_MID, 0,\n               -(bottom + lv_font_get_line_height(options.small_font) +\n                 lv_font_get_line_height(options.text_font) + gui2_core::ui_px(12)));\n  return view;\n}\n\nbool splash_intro_finished() {',
    ),
]


def main(core):
    updates = []
    for relative, original_sha, patched_sha, old, new in PATCHES:
        path = core / relative
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if digest == patched_sha:
            continue
        if digest != original_sha:
            raise SystemExit(f'Unexpected pinned source in {relative}; splash patch not applied')
        source = data.decode('utf-8')
        if source.count(old) != 1:
            raise SystemExit(f'Unexpected splash anchor in {relative}')
        result = source.replace(old, new).encode('utf-8')
        if hashlib.sha256(result).hexdigest() != patched_sha:
            raise SystemExit(f'Unexpected splash result in {relative}')
        updates.append((path, result))
    # Validate every input before changing any file.
    for path, data in updates:
        path.write_bytes(data)
    print('Pinned GUI2: minimum normal splash 4000 ms; maintainer ZC_J1an9')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: fix-splash-branding.py /path/to/bootable/recovery')
    main(Path(sys.argv[1]))
