#!/usr/bin/env python3

"""
Disassemble a GameBoy ROM into Z80 assembly code in rgbds syntax.
"""

__author__  = 'Rangi'
__version__ = '1.8.1'

import sys
import os.path
from collections import defaultdict


starting_points = set()
labels = defaultdict(lambda: set())
raw_data = {}
left_data = {}
data_size = 0
operations = {}
terminate = False


def signed(b):
	return b - 0x100 if b >= 0x80 else b

def u8(b):
	return '$%02x' % b

def s8(b, plus=False):
	b = signed(b)
	return ('-' if b < 0 else '+' if plus else '') + '$%x' % abs(b)

def u16le(lo, hi):
	return '$%04x' % (hi << 8 | lo)


def create_db(pc, *args):
	return 'db ' + ', '.join(u8(b) for b in args)


def format_label(target):
	return 'Function%04x' % target

def format_address(address):
	return '%06x' % address

def format_bytes(bytes):
	return ' '.join('%02x' % b for b in bytes)

def bank_offset_to_address(bank_offset):
	bank, offset = bank_offset.split(':')
	bank = int(bank, 16)
	offset = int(offset, 16)
	if bank > 0x00:
		bank -= 1
	return bank * 0x4000 + offset


def parse_symfile(filename):
	with open(filename, 'r') as f:
		lines = f.readlines()
	labels = defaultdict(lambda: set())
	for line in lines:
		line = line.split(';')[0].strip()
		if not line:
			continue
		bank_offset, label = line.split()
		address = bank_offset_to_address(bank_offset)
		labels[address].add(label)
	return labels


def create_ret(pc):
	global terminate
	terminate = True
	return 'ret'

def create_jp_hl(pc):
	global terminate
	terminate = True
	return 'jp hl'

def create_jr(pc, offset, condition=None):
	global terminate
	if not condition:
		terminate = True
	target = pc + 2 + signed(offset)
	return create_branch('jr', target, condition)

def create_jp(pc, lo, hi, condition=None):
	global terminate
	if not condition:
		terminate = True
	target = hi << 8 | lo
	return create_branch('jp', target, condition)

def create_call(pc, lo, hi, condition=None):
	target = hi << 8 | lo
	return create_branch('call', target, condition)

def create_branch(op, target, condition=None):
	global starting_points, labels
	starting_points.add(target)
	if target in labels:
		label = next(iter(labels[target]))
	else:
		label = format_label(target)
		labels[target].add(label)
	if condition:
		return '%s %s, %s' % (op, condition, label)
	return '%s %s' % (op, label)


def get_prefix_opcode(pc, b):
	ops = (['rlc', 'rrc', 'rl', 'rr', 'sla', 'sra', 'swap', 'srl'] +
		['bit %d,' % i for i in range(8)] + ['res %d,' % i for i in range(8)] +
		['set %d,' % i for i in range(8)])
	args = ['b', 'c', 'd', 'e', 'h', 'l', '[hl]', 'a']
	op, arg = divmod(b, 8)
	return '%s %s' % (ops[op], args[arg])


opcode_table = [
	(0, lambda pc: 'nop'),                               # 00 - nop
	(2, lambda pc, a, b: 'ld bc, %s' % u16le(a, b)),     # 01 - ld bc, d16
	(0, lambda pc: 'ld bc, a'),                          # 02 - ld bc, a
	(0, lambda pc: 'inc bc'),                            # 03 - inc bc
	(0, lambda pc: 'inc b'),                             # 04 - inc b
	(0, lambda pc: 'dec b'),                             # 05 - dec b
	(1, lambda pc, a: 'ld b, %s' % u8(a)),               # 06 - ld b, d8
	(0, lambda pc: 'rlca'),                              # 07 - rlca
	(2, lambda pc, a, b: 'ld [%s], sp' % u16le(a, b)),   # 08 - ld [d16], sp
	(0, lambda pc: 'add hl, bc'),                        # 09 - add hl, bc
	(0, lambda pc: 'ld a, [bc]'),                        # 0a - ld a, [bc]
	(0, lambda pc: 'dec bc'),                            # 0b - dec bc
	(0, lambda pc: 'inc c'),                             # 0c - inc c
	(0, lambda pc: 'dec c'),                             # 0d - dec c
	(1, lambda pc, a: 'ld c, %s' % u8(a)),               # 0e - ld c, d8
	(0, lambda pc: 'rrca'),                              # 0f - rrca
	(0, lambda pc: 'stop'),                              # 10 - stop
	(2, lambda pc, a, b: 'ld de, %s' % u16le(a, b)),     # 11 - ld de, d16
	(0, lambda pc: 'ld [de], a'),                        # 12 - ld [de], a
	(0, lambda pc: 'inc de'),                            # 13 - inc de
	(0, lambda pc: 'inc d'),                             # 14 - inc d
	(0, lambda pc: 'dec d'),                             # 15 - dec d
	(1, lambda pc, a: 'ld d, %s' % u8(a)),               # 16 - ld d, d8
	(0, lambda pc: 'rla'),                               # 17 - rla
	(1, create_jr),                                      # 18 - jr r8
	(0, lambda pc: 'add hl, de'),                        # 19 - add hl, de
	(0, lambda pc: 'ld a, [de]'),                        # 1a - ld a, [de]
	(0, lambda pc: 'dec de'),                            # 1b - dec de
	(0, lambda pc: 'inc e'),                             # 1c - inc e
	(0, lambda pc: 'dec e'),                             # 1d - dec e
	(1, lambda pc, a: 'ld e, %s' % u8(a)),               # 1e - ld e, d8
	(0, lambda pc: 'rra'),                               # 1f - rra
	(1, lambda pc, a: create_jr(pc, a, 'nz')),           # 20 - jr nz, r8
	(2, lambda pc, a, b: 'ld hl, %s' % u16le(a, b)),     # 21 - ld hl, d16
	(0, lambda pc: 'ld [hli], a'),                       # 22 - ld [hli], a
	(0, lambda pc: 'inc hl'),                            # 23 - inc hl
	(0, lambda pc: 'inc h'),                             # 24 - inc h
	(0, lambda pc: 'dec h'),                             # 25 - dec h
	(1, lambda pc, a: 'ld h, %s' % u8(a)),               # 26 - ld h, d8
	(0, lambda pc: 'daa'),                               # 27 - daa
	(1, lambda pc, a: create_jr(pc, a, 'z')),            # 28 - jr z, r8
	(0, lambda pc: 'add hl, hl'),                        # 29 - add hl, hl
	(0, lambda pc: 'ld a, [hli]'),                       # 2a - ld a, [dli]
	(0, lambda pc: 'dec hl'),                            # 2b - dec hl
	(0, lambda pc: 'inc l'),                             # 2c - inc l
	(0, lambda pc: 'dec l'),                             # 2d - dec l
	(1, lambda pc, a: 'ld l, %s' % u8(a)),               # 2e - ld l, d8
	(0, lambda pc: 'cpl'),                               # 2f - cpl
	(1, lambda pc, a: create_jr(pc, a, 'nc')),           # 30 - jr nc, r8
	(2, lambda pc, a, b: 'ld sp, %s' % u16le(a, b)),     # 31 - ld sp, d16
	(0, lambda pc: 'ld [hld], a'),                       # 32 - ld [hld], a
	(0, lambda pc: 'inc sp'),                            # 33 - inc sp
	(0, lambda pc: 'inc [hl]'),                          # 34 - inc [hl]
	(0, lambda pc: 'dec [hl]'),                          # 35 - dec [hl]
	(1, lambda pc, a: 'ld [hl], %s' % u8(a)),            # 36 - ld [hl], d8
	(0, lambda pc: 'scf'),                               # 37 - scf
	(1, lambda pc, a: create_jr(pc, a, 'c')),            # 38 - jr c, r8
	(0, lambda pc: 'add hl, sp'),                        # 39 - add hl, sp
	(0, lambda pc: 'ld a, [hld]'),                       # 3a - ld a, [hld]
	(0, lambda pc: 'dec sp'),                            # 3b - dec sp
	(0, lambda pc: 'inc a'),                             # 3c - inc a
	(0, lambda pc: 'dec a'),                             # 3d - dec a
	(1, lambda pc, a: 'ld a, %s' % u8(a)),               # 3e - ld a, d8
	(0, lambda pc: 'ccf'),                               # 3f - ccf
	(0, lambda pc: 'ld b, b'),                           # 40 - ld b, b
	(0, lambda pc: 'ld b, c'),                           # 41 - ld b, c
	(0, lambda pc: 'ld b, d'),                           # 42 - ld b, d
	(0, lambda pc: 'ld b, e'),                           # 43 - ld b, e
	(0, lambda pc: 'ld b, h'),                           # 44 - ld b, h
	(0, lambda pc: 'ld b, l'),                           # 45 - ld b, l
	(0, lambda pc: 'ld b, [hl]'),                        # 46 - ld b, [hl]
	(0, lambda pc: 'ld b, a'),                           # 47 - ld b, a
	(0, lambda pc: 'ld c, b'),                           # 48 - ld c, b
	(0, lambda pc: 'ld c, c'),                           # 49 - ld c, c
	(0, lambda pc: 'ld c, d'),                           # 4a - ld c, d
	(0, lambda pc: 'ld c, e'),                           # 4b - ld c, e
	(0, lambda pc: 'ld c, h'),                           # 4c - ld c, h
	(0, lambda pc: 'ld c, l'),                           # 4d - ld c, l
	(0, lambda pc: 'ld c, [hl]'),                        # 4e - ld c, [hl]
	(0, lambda pc: 'ld c, a'),                           # 4f - ld c, a
	(0, lambda pc: 'ld d, b'),                           # 50 - ld d, b
	(0, lambda pc: 'ld d, c'),                           # 51 - ld d, c
	(0, lambda pc: 'ld d, d'),                           # 52 - ld d, d
	(0, lambda pc: 'ld d, e'),                           # 53 - ld d, e
	(0, lambda pc: 'ld d, h'),                           # 54 - ld d, h
	(0, lambda pc: 'ld d, l'),                           # 55 - ld d, l
	(0, lambda pc: 'ld d, [hl]'),                        # 56 - ld d, [hl]
	(0, lambda pc: 'ld d, a'),                           # 57 - ld d, a
	(0, lambda pc: 'ld e, b'),                           # 58 - ld e, b
	(0, lambda pc: 'ld e, c'),                           # 59 - ld e, c
	(0, lambda pc: 'ld e, d'),                           # 5a - ld e, d
	(0, lambda pc: 'ld e, e'),                           # 5b - ld e, e
	(0, lambda pc: 'ld e, h'),                           # 5c - ld e, h
	(0, lambda pc: 'ld e, l'),                           # 5d - ld e, l
	(0, lambda pc: 'ld e, [hl]'),                        # 5e - ld e, [hl]
	(0, lambda pc: 'ld e, a'),                           # 5f - ld e, a
	(0, lambda pc: 'ld h, b'),                           # 60 - ld h, b
	(0, lambda pc: 'ld h, c'),                           # 61 - ld h, c
	(0, lambda pc: 'ld h, d'),                           # 62 - ld h, d
	(0, lambda pc: 'ld h, e'),                           # 63 - ld h, e
	(0, lambda pc: 'ld h, h'),                           # 64 - ld h, h
	(0, lambda pc: 'ld h, l'),                           # 65 - ld h, l
	(0, lambda pc: 'ld h, [hl]'),                        # 66 - ld h, [hl]
	(0, lambda pc: 'ld h, a'),                           # 67 - ld h, a
	(0, lambda pc: 'ld l, b'),                           # 68 - ld l, b
	(0, lambda pc: 'ld l, c'),                           # 69 - ld l, c
	(0, lambda pc: 'ld l, d'),                           # 6a - ld l, d
	(0, lambda pc: 'ld l, e'),                           # 6b - ld l, e
	(0, lambda pc: 'ld l, h'),                           # 6c - ld l, h
	(0, lambda pc: 'ld l, l'),                           # 6d - ld l, l
	(0, lambda pc: 'ld l, [hl]'),                        # 6e - ld l, [hl]
	(0, lambda pc: 'ld l, a'),                           # 6f - ld l, a
	(0, lambda pc: 'ld [hl], b'),                        # 70 - ld [hl], b
	(0, lambda pc: 'ld [hl], c'),                        # 71 - ld [hl], c
	(0, lambda pc: 'ld [hl], d'),                        # 72 - ld [hl], d
	(0, lambda pc: 'ld [hl], e'),                        # 73 - ld [hl], e
	(0, lambda pc: 'ld [hl], h'),                        # 74 - ld [hl], h
	(0, lambda pc: 'ld [hl], l'),                        # 75 - ld [hl], l
	(0, lambda pc: 'halt'),                              # 76 - halt
	(0, lambda pc: 'ld [hl], a'),                        # 77 - ld [hl], a
	(0, lambda pc: 'ld a, b'),                           # 78 - ld a, b
	(0, lambda pc: 'ld a, c'),                           # 79 - ld a, c
	(0, lambda pc: 'ld a, d'),                           # 7a - ld a, d
	(0, lambda pc: 'ld a, e'),                           # 7b - ld a, e
	(0, lambda pc: 'ld a, h'),                           # 7c - ld a, h
	(0, lambda pc: 'ld a, l'),                           # 7d - ld a, l
	(0, lambda pc: 'ld a, [hl]'),                        # 7e - ld a, [hl]
	(0, lambda pc: 'ld a, a'),                           # 7f - ld a, a
	(0, lambda pc: 'add b'),                             # 80 - add b
	(0, lambda pc: 'add c'),                             # 81 - add c
	(0, lambda pc: 'add d'),                             # 82 - add d
	(0, lambda pc: 'add e'),                             # 83 - add e
	(0, lambda pc: 'add h'),                             # 84 - add h
	(0, lambda pc: 'add l'),                             # 85 - add l
	(0, lambda pc: 'add [hl]'),                          # 86 - add [hl]
	(0, lambda pc: 'add a'),                             # 87 - add a
	(0, lambda pc: 'adc b'),                             # 88 - adc b
	(0, lambda pc: 'adc c'),                             # 89 - adc c
	(0, lambda pc: 'adc d'),                             # 8a - adc d
	(0, lambda pc: 'adc e'),                             # 8b - adc e
	(0, lambda pc: 'adc h'),                             # 8c - adc h
	(0, lambda pc: 'adc l'),                             # 8d - adc l
	(0, lambda pc: 'adc [hl]'),                          # 8e - adc [hl]
	(0, lambda pc: 'adc a'),                             # 8f - adc a
	(0, lambda pc: 'sub b'),                             # 90 - sub b
	(0, lambda pc: 'sub c'),                             # 91 - sub c
	(0, lambda pc: 'sub d'),                             # 92 - sub d
	(0, lambda pc: 'sub e'),                             # 93 - sub e
	(0, lambda pc: 'sub h'),                             # 94 - sub h
	(0, lambda pc: 'sub l'),                             # 95 - sub l
	(0, lambda pc: 'sub [hl]'),                          # 96 - sub [hl]
	(0, lambda pc: 'sub a'),                             # 97 - sub a
	(0, lambda pc: 'sbc b'),                             # 98 - sbc b
	(0, lambda pc: 'sbc c'),                             # 99 - sbc c
	(0, lambda pc: 'sbc d'),                             # 9a - sbc d
	(0, lambda pc: 'sbc e'),                             # 9b - sbc e
	(0, lambda pc: 'sbc h'),                             # 9c - sbc h
	(0, lambda pc: 'sbc l'),                             # 9d - sbc l
	(0, lambda pc: 'sbc [hl]'),                          # 9e - sbc [hl]
	(0, lambda pc: 'sbc a'),                             # 9f - sbc a
	(0, lambda pc: 'and b'),                             # a0 - and b
	(0, lambda pc: 'and c'),                             # a1 - and c
	(0, lambda pc: 'and d'),                             # a2 - and d
	(0, lambda pc: 'and e'),                             # a3 - and e
	(0, lambda pc: 'and h'),                             # a4 - and h
	(0, lambda pc: 'and l'),                             # a5 - and l
	(0, lambda pc: 'and [hl]'),                          # a6 - and [hl]
	(0, lambda pc: 'and a'),                             # a7 - and a
	(0, lambda pc: 'xor b'),                             # a8 - xor b
	(0, lambda pc: 'xor c'),                             # a9 - xor c
	(0, lambda pc: 'xor d'),                             # aa - xor d
	(0, lambda pc: 'xor e'),                             # ab - xor e
	(0, lambda pc: 'xor h'),                             # ac - xor h
	(0, lambda pc: 'xor l'),                             # ad - xor l
	(0, lambda pc: 'xor [hl]'),                          # ae - xor [hl]
	(0, lambda pc: 'xor a'),                             # af - xor a
	(0, lambda pc: 'or b'),                              # b0 - or b
	(0, lambda pc: 'or c'),                              # b1 - or c
	(0, lambda pc: 'or d'),                              # b2 - or d
	(0, lambda pc: 'or e'),                              # b3 - or e
	(0, lambda pc: 'or h'),                              # b4 - or h
	(0, lambda pc: 'or l'),                              # b5 - or l
	(0, lambda pc: 'or [hl]'),                           # b6 - or [hl]
	(0, lambda pc: 'or a'),                              # b7 - or a
	(0, lambda pc: 'cp b'),                              # b8 - cp b
	(0, lambda pc: 'cp c'),                              # b9 - cp c
	(0, lambda pc: 'cp d'),                              # ba - cp d
	(0, lambda pc: 'cp e'),                              # bb - cp e
	(0, lambda pc: 'cp h'),                              # bc - cp h
	(0, lambda pc: 'cp l'),                              # bd - cp l
	(0, lambda pc: 'cp [hl]'),                           # be - cp [hl]
	(0, lambda pc: 'cp a'),                              # bf - cp a
	(0, lambda pc: 'ret nz'),                            # c0 - ret nz
	(0, lambda pc: 'pop bc'),                            # c1 - pop bc
	(2, lambda pc, a, b: create_jp(pc, a, b, 'nz')),     # c2 - jp nz, a16
	(2, create_jp),                                      # c3 - jp a16
	(2, lambda pc, a, b: create_call(pc, a, b, 'nz')),   # c4 - call nz, a16
	(0, lambda pc: 'push bc'),                           # c5 - push bc
	(1, lambda pc, a: 'add %s' % u8(a)),                 # c6 - add d8
	(0, lambda pc: 'rst $0'),                            # c7 - rst $0
	(0, lambda pc: 'ret z'),                             # c8 - ret z
	(0, create_ret),                                     # c9 - ret
	(2, lambda pc, a, b: create_jp(pc, a, b, 'z')),      # ca - jp z, a16
	(1, get_prefix_opcode),                              # cb - prefix
	(2, lambda pc, a, b: create_call(pc, a, b, 'z')),    # cc - call z, a16
	(2, create_call),                                    # cd - call a16
	(1, lambda pc, a: 'adc %s' % u8(a)),                 # ce - adc d8
	(0, lambda pc: 'rst $8'),                            # cf - rst $8
	(0, lambda pc: 'ret nc'),                            # d0 - ret nc
	(0, lambda pc: 'pop de'),                            # d1 - pop de
	(2, lambda pc, a, b: create_jp(pc, a, b, 'nc')),     # d2 - jp nc, a16
	(0, lambda pc: 'db $d3'),                            # d3 -
	(2, lambda pc, a, b: create_call(pc, a, b, 'nc')),   # d4 - call nc, a16
	(0, lambda pc: 'push de'),                           # d5 - push de
	(1, lambda pc, a: 'sub %s' % u8(a)),                 # d6 - sub d8
	(0, lambda pc: 'rst $10'),                           # d7 - rst $10
	(0, lambda pc: 'ret c'),                             # d8 - ret c
	(0, lambda pc: 'reti'),                              # d9 - reti
	(2, lambda pc, a, b: create_jp(pc, a, b, 'c')),      # da - jp c, a16
	(0, lambda pc: 'db $db'),                            # db -
	(2, lambda pc, a, b: create_call(pc, a, b, 'c')),    # dc - call c, a16
	(0, lambda pc: 'db $dd'),                            # dd -
	(1, lambda pc, a: 'sbc %s' % u8(a)),                 # de - sbc d8
	(0, lambda pc: 'rst $18'),                           # df - rst $18
	(1, lambda pc, a: create_ldh_to(a)),                 # e0 - ld [$ff00+a8], a
	(0, lambda pc: 'pop hl'),                            # e1 - pop hl
	(0, lambda pc: 'ld [$ff00+c], a'),                   # e2 - ld [$ff00+c], a
	(0, lambda pc: 'db $e3'),                            # e3 -
	(0, lambda pc: 'db $e4'),                            # e4 -
	(0, lambda pc: 'push hl'),                           # e5 - push hl
	(1, lambda pc, a: 'and %s' % u8(a)),                 # e6 - and d8
	(0, lambda pc: 'rst $20'),                           # e7 - rst $20
	(1, lambda pc, a: 'add sp, %s' % s8(a, plus=False)), # e8 - add sp, r8
	(0, create_jp_hl),                                   # e9 - jp hl
	(2, lambda pc, a, b: 'ld [%s], a' % u16le(a, b)),    # ea - ld [a16], a
	(0, lambda pc: 'db $eb'),                            # eb -
	(0, lambda pc: 'db $ec'),                            # ec -
	(0, lambda pc: 'db $ed'),                            # ed -
	(1, lambda pc, a: 'xor %s' % u8(a)),                 # ee - xor d8
	(0, lambda pc: 'rst $28'),                           # ef - rst $28
	(1, lambda pc, a: create_ldh_from(a)),               # f0 - ld a, [$ff00+a8]
	(0, lambda pc: 'pop af'),                            # f1 - pop af
	(0, lambda pc: 'ld a, [$ff00+c]'),                   # f2 - ld a, [$ff00+c]
	(0, lambda pc: 'di'),                                # f3 - di
	(0, lambda pc: 'db $f4'),                            # f4 -
	(0, lambda pc: 'push af'),                           # f5 - push af
	(1, lambda pc, a: 'or %s' % u8(a)),                  # f6 - or d8
	(0, lambda pc: 'rst $30'),                           # f7 - rst $30
	(1, lambda pc, a: 'ld hl, sp%s' % s8(a, plus=True)), # f8 - ld hl, sp+r8
	(0, lambda pc: 'ld sp, hl'),                         # f9 - ld sp, hl
	(2, lambda pc, a, b: 'ld a, [%s]' % u16le(a, b)),    # fa - ld a, [a16]
	(0, lambda pc: 'ei'),                                # fb - ei
	(0, lambda pc: 'db $fc'),                            # fc -
	(0, lambda pc: 'db $fd'),                            # fd -
	(1, lambda pc, a: 'cp %s' % u8(a)),                  # fe - cp d8
	(0, lambda pc: 'rst $38'),                           # ff - rst $38
]


def disassemble(filename, entry_point=0x000000):
	global raw_data, left_data, data_size, starting_points, operations

	with open(filename, 'rb') as f:
		raw_data = dict(enumerate(f.read()))
		data_size = len(raw_data)
		left_data = raw_data.copy()

	starting_points.add(entry_point)

	while starting_points:
		pc = starting_points.pop()
		if pc in left_data:
			disassemble_from(pc)

	pc = 0
	LINE_LENGTH = 50
	while pc < data_size:
		if pc in labels:
			for label in labels[pc]:
				print(label + ':')

		if pc in operations:
			operation, bytes = operations[pc]
			line = '%s%s' % (operation, ' ' * max(LINE_LENGTH - len(operation), 1))
			print('\t%s; %s: %s' % (line, format_address(pc), format_bytes(bytes)))
			pc += 1

		elif pc in left_data:
			chunk_pc = pc
			CHUNK_SIZE = 8
			data = []
			while pc in left_data:
				data.append(left_data[pc])
				pc += 1
			while data:
				chunk, data = data[:CHUNK_SIZE], data[CHUNK_SIZE:]
				dbs = create_db(chunk_pc, *chunk)
				line = '%s%s' % (dbs, ' ' * max(LINE_LENGTH - len(dbs), 1))
				print('\t%s; %s-%s' % (line, format_address(chunk_pc),
					format_address(chunk_pc + len(chunk) - 1)))
				chunk_pc += CHUNK_SIZE

		else:
			pc += 1


def disassemble_from(pc):
	global raw_data, left_data, operations, terminate

	terminate = False

	while pc < data_size:
		if pc not in left_data:
			return
		opcode = left_data[pc]
		width, get_operation = opcode_table[opcode]

		if pc + width < data_size:
			args = [raw_data[pc + 1 + i] for i in range(width)]
			operations[pc] = (get_operation(pc, *args), [opcode] + args)
		else:
			bytes = [raw_data[a] for a in range(pc, data_size)]
			operations[pc] = (create_db(pc, *bytes), bytes)

		for i in range(pc, min(pc + 1 + width, data_size)):
			if i in left_data:
				del left_data[i]

		if terminate:
			return

		pc += 1 + width


def create_ldh_to(a):
	return 'ld [%s], a' % gbhw_register_table.get(a, '$ff00+' + u8(a))

def create_ldh_from(a):
	return 'ld a, [%s]' % gbhw_register_table.get(a, '$ff00+' + u8(a))

gbhw_register_table = {
	0x00: 'rJOYP',     # Joypad (R/W)
	0x01: 'rSB',       # Serial transfer data (R/W)
	0x02: 'rSC',       # Serial Transfer Control (R/W)
	0x04: 'rDIV',      # Divider Register (R/W)
	0x05: 'rTIMA',     # Timer counter (R/W)
	0x06: 'rTMA',      # Timer Modulo (R/W)
	0x07: 'rTAC',      # Timer Control (R/W)
	0x0f: 'rIF',       # Interrupt Flag (R/W)
	0x10: 'rNR10',     # Channel 1 Sweep register (R/W)
	0x11: 'rNR11',     # Channel 1 Sound length/Wave pattern duty (R/W)
	0x12: 'rNR12',     # Channel 1 Volume Envelope (R/W)
	0x13: 'rNR13',     # Channel 1 Frequency lo (Write Only)
	0x14: 'rNR14',     # Channel 1 Frequency hi (R/W)
	0x15: 'rNR20',     # Channel 2 Sweep register (R/W)
	0x16: 'rNR21',     # Channel 2 Sound Length/Wave Pattern Duty (R/W)
	0x17: 'rNR22',     # Channel 2 Volume Envelope (R/W)
	0x18: 'rNR23',     # Channel 2 Frequency lo data (W)
	0x19: 'rNR24',     # Channel 2 Frequency hi data (R/W)
	0x1a: 'rNR30',     # Channel 3 Sound on/off (R/W)
	0x1b: 'rNR31',     # Channel 3 Sound Length
	0x1c: 'rNR32',     # Channel 3 Select output level (R/W)
	0x1d: 'rNR33',     # Channel 3 Frequency's lower data (W)
	0x1e: 'rNR34',     # Channel 3 Frequency's higher data (R/W)
	0x1f: 'rNR40',     # Channel 4 Sweep register (R/W)
	0x20: 'rNR41',     # Channel 4 Sound Length (R/W)
	0x21: 'rNR42',     # Channel 4 Volume Envelope (R/W)
	0x22: 'rNR43',     # Channel 4 Polynomial Counter (R/W)
	0x23: 'rNR44',     # Channel 4 Counter/consecutive; Inital (R/W)
	0x24: 'rNR50',     # Channel control / ON-OFF / Volume (R/W)
	0x25: 'rNR51',     # Selection of Sound output terminal (R/W)
	0x26: 'rNR52',     # Sound on/off
	0x30: 'rWave_0',
	0x31: 'rWave_1',
	0x32: 'rWave_2',
	0x33: 'rWave_3',
	0x34: 'rWave_4',
	0x35: 'rWave_5',
	0x36: 'rWave_6',
	0x37: 'rWave_7',
	0x38: 'rWave_8',
	0x39: 'rWave_9',
	0x3a: 'rWave_a',
	0x3b: 'rWave_b',
	0x3c: 'rWave_c',
	0x3d: 'rWave_d',
	0x3e: 'rWave_e',
	0x3f: 'rWave_f',
	0x40: 'rLCDC',     # LCD Control (R/W)
	0x41: 'rSTAT',     # LCDC Status (R/W)
	0x42: 'rSCY',      # Scroll Y (R/W)
	0x43: 'rSCX',      # Scroll X (R/W)
	0x44: 'rLY',       # LCDC Y-Coordinate (R)
	0x45: 'rLYC',      # LY Compare (R/W)
	0x46: 'rDMA',      # DMA Transfer and Start Address (W)
	0x47: 'rBGP',      # BG Palette Data (R/W) - Non CGB Mode Only
	0x48: 'rOBP0',     # Object Palette 0 Data (R/W) - Non CGB Mode Only
	0x49: 'rOBP1',     # Object Palette 1 Data (R/W) - Non CGB Mode Only
	0x4a: 'rWY',       # Window Y Position (R/W)
	0x4b: 'rWX',       # Window X Position minus 7 (R/W)
	0x4c: 'rLCDMODE',
	0x4d: 'rKEY1',     # CGB Mode Only - Prepare Speed Switch
	0x4f: 'rVBK',      # CGB Mode Only - VRAM Bank
	0x50: 'rBLCK',
	0x51: 'rHDMA1',    # CGB Mode Only - New DMA Source, High
	0x52: 'rHDMA2',    # CGB Mode Only - New DMA Source, Low
	0x53: 'rHDMA3',    # CGB Mode Only - New DMA Destination, High
	0x54: 'rHDMA4',    # CGB Mode Only - New DMA Destination, Low
	0x55: 'rHDMA5',    # CGB Mode Only - New DMA Length/Mode/Start
	0x56: 'rRP',       # CGB Mode Only - Infrared Communications Port
	0x68: 'rBGPI',     # CGB Mode Only - Background Palette Index
	0x69: 'rBGPD',     # CGB Mode Only - Background Palette Data
	0x6a: 'rOBPI',     # CGB Mode Only - Sprite Palette Index
	0x6b: 'rOBPD',     # CGB Mode Only - Sprite Palette Data
	0x6c: 'rUNKNOWN1', # (FEh) Bit 0 (Read/Write) - CGB Mode Only
	0x70: 'rSVBK',     # CGB Mode Only - WRAM Bank
	0x72: 'rUNKNOWN2', # (00h) - Bit 0-7 (Read/Write)
	0x73: 'rUNKNOWN3', # (00h) - Bit 0-7 (Read/Write)
	0x74: 'rUNKNOWN4', # (00h) - Bit 0-7 (Read/Write) - CGB Mode Only
	0x75: 'rUNKNOWN5', # (8Fh) - Bit 4-6 (Read/Write)
	0x76: 'rUNKNOWN6', # (00h) - Always 00h (Read Only)
	0x77: 'rUNKNOWN7', # (00h) - Always 00h (Read Only)
	0xff: 'rIE',       # Interrupt Enable (R/W)
}


def usage_exit():
	print('Usage: %s a.bin [a.sym] [entry_point]' % sys.argv[0], file=sys.stderr)
	sys.exit(1)

def main():
	global starting_points, labels

	argc = len(sys.argv)
	if argc < 2:
		usage_exit()
	bin_filename = sys.argv[1]
	sym_filename = None
	entry_point = 0x000000
	if argc == 4:
		sym_filename = sys.argv[2]
		entry_point = int(sys.argv[3], 16)
	elif argc == 3:
		if set(sys.argv[2].lower()) - set('0123456789abcdef'):
			sym_filename = sys.argv[2]
		else:
			entry_point = int(sys.argv[2], 16)
	elif argc != 2:
		usage_exit()

	if sym_filename:
		sym_labels = parse_symfile(sym_filename)
		labels.update(sym_labels)
		starting_points.update(sym_labels.keys())

	labels[entry_point].add('ENTRY_POINT')

	disassemble(sys.argv[1], entry_point)

if __name__ == '__main__':
	main()
