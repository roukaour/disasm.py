# disasm.py

Disassemble a GameBoy ROM into Z80 assembly code in [rgbds](https://github.com/rednex/rgbds) syntax.

Usage:

    $ ./disasm.py a.bin > a.asm

Or to specify an entry point other than the start of the file, e.g. address `$10ab`:

    $ ./disasm.py a.bin 10ab > a.asm

Uses hardware register names from [gbhw.asm](https://github.com/pret/pokecrystal/blob/master/gbhw.asm).

Discuss on [Skeetendo](https://hax.iimarckus.org/topic/7161/).
