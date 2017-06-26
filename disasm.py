#!/usr/bin/env python3

"""
Disassemble a GameBoy ROM into Z80 assembly code in rgbds syntax.
"""

__author__  = "Rangi"
__version__ = "1.2"

import sys
import os.path
from collections import defaultdict


starting_points = set()
labels = defaultdict(lambda: set())
raw_data = {}
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
	label = format_label(target)
	labels[target].add(label)
	if condition:
		return '%s %s, %s' % (op, condition, label)
	return '%s %s' % (op, label)


def get_prefix_opcode(pc, b):
	ops = [
		'rlc', 'rrc', 'rl', 'rr', 'sla', 'sra', 'swap', 'srl',
		'bit 0,', 'bit 1,', 'bit 2,', 'bit 3,', 'bit 4,', 'bit 5,', 'bit 6,', 'bit 7,',
		'res 0,', 'res 1,', 'res 2,', 'res 3,', 'res 4,', 'res 5,', 'res 6,', 'res 7,',
		'set 0,', 'set 1,', 'set 2,', 'set 3,', 'set 4,', 'set 5,', 'set 6,', 'set 7,',
	]
	args = ['b', 'c', 'd', 'e', 'h', 'l', '[hl]', 'a']
	op, arg = divmod(b, 8)
	return '%s %s' % (ops[op], args[arg])


opcode_table = [
	(0, lambda pc: 'nop'),                               # 00
	(2, lambda pc, a, b: 'ld bc, %s' % u16le(a, b)),     # 01
	(0, lambda pc: 'ld bc, a'),                          # 02
	(0, lambda pc: 'inc bc'),                            # 03
	(0, lambda pc: 'inc b'),                             # 04
	(0, lambda pc: 'dec b'),                             # 05
	(1, lambda pc, a: 'ld b, %s' % u8(a)),               # 06
	(0, lambda pc: 'rlc a'),                             # 07
	(2, lambda pc, a, b: 'ld [%s], sp' % u16le(a, b)),   # 08
	(0, lambda pc: 'add hl, bc'),                        # 09
	(0, lambda pc: 'ld a, [bc]'),                        # 0a
	(0, lambda pc: 'dec bc'),                            # 0b
	(0, lambda pc: 'inc c'),                             # 0c
	(0, lambda pc: 'dec c'),                             # 0d
	(1, lambda pc, a: 'ld c, %s' % u8(a)),               # 0e
	(0, lambda pc: 'rrc a'),                             # 0f
	(0, lambda pc: 'stop'),                              # 10
	(2, lambda pc, a, b: 'ld de, %s' % u16le(a, b)),     # 11
	(0, lambda pc: 'ld [de], a'),                        # 12
	(0, lambda pc: 'inc de'),                            # 13
	(0, lambda pc: 'inc d'),                             # 14
	(0, lambda pc: 'dec d'),                             # 15
	(1, lambda pc, a: 'ld d, %s' % u8(a)),               # 16
	(0, lambda pc: 'rla'),                               # 17
	(1, create_jr),                                      # 18
	(0, lambda pc: 'add hl, de'),                        # 19
	(0, lambda pc: 'ld a, [de]'),                        # 1a
	(0, lambda pc: 'dec de'),                            # 1b
	(0, lambda pc: 'inc e'),                             # 1c
	(0, lambda pc: 'dec e'),                             # 1d
	(1, lambda pc, a: 'ld e, %s' % u8(a)),               # 1e
	(0, lambda pc: 'rra'),                               # 1f
	(1, lambda pc, a: create_jr(pc, a, 'nz')),           # 20
	(2, lambda pc, a, b: 'ld hl, %s' % u16le(a, b)),     # 21
	(0, lambda pc: 'ld [hli], a'),                       # 22
	(0, lambda pc: 'inc hl'),                            # 23
	(0, lambda pc: 'inc h'),                             # 24
	(0, lambda pc: 'dec h'),                             # 25
	(1, lambda pc, a: 'ld h, %s' % u8(a)),               # 26
	(0, lambda pc: 'daa'),                               # 27
	(1, lambda pc, a: create_jr(pc, a, 'z')),            # 28
	(0, lambda pc: 'add hl, hl'),                        # 29
	(0, lambda pc: 'ld a, [hli]'),                       # 2a
	(0, lambda pc: 'dec hl'),                            # 2b
	(0, lambda pc: 'inc l'),                             # 2c
	(0, lambda pc: 'dec l'),                             # 2d
	(1, lambda pc, a: 'ld l, %s' % u8(a)),               # 2e
	(0, lambda pc: 'cpl'),                               # 2f
	(1, lambda pc, a: create_jr(pc, a, 'nc')),           # 30
	(2, lambda pc, a, b: 'ld sp, %s' % u16le(a, b)),     # 31
	(0, lambda pc: 'ld [hld], a'),                       # 32
	(0, lambda pc: 'inc sp'),                            # 33
	(0, lambda pc: 'inc [hl]'),                          # 34
	(0, lambda pc: 'dec [hl]'),                          # 35
	(1, lambda pc, a: 'ld [hl], %s' % u8(a)),            # 36
	(0, lambda pc: 'scf'),                               # 37
	(1, lambda pc, a: create_jr(pc, a, 'c')),            # 38
	(0, lambda pc: 'add hl, sp'),                        # 39
	(0, lambda pc: 'ld a, [hld]'),                       # 3a
	(0, lambda pc: 'dec sp'),                            # 3b
	(0, lambda pc: 'inc a'),                             # 3c
	(0, lambda pc: 'dec a'),                             # 3d
	(1, lambda pc, a: 'ld a, %s' % u8(a)),               # 3e
	(0, lambda pc: 'ccf'),                               # 3f
	(0, lambda pc: 'ld b, b'),                           # 40
	(0, lambda pc: 'ld b, c'),                           # 41
	(0, lambda pc: 'ld b, d'),                           # 42
	(0, lambda pc: 'ld b, e'),                           # 43
	(0, lambda pc: 'ld b, h'),                           # 44
	(0, lambda pc: 'ld b, l'),                           # 45
	(0, lambda pc: 'ld b, [hl]'),                        # 46
	(0, lambda pc: 'ld b, a'),                           # 47
	(0, lambda pc: 'ld c, b'),                           # 48
	(0, lambda pc: 'ld c, c'),                           # 49
	(0, lambda pc: 'ld c, d'),                           # 4a
	(0, lambda pc: 'ld c, e'),                           # 4b
	(0, lambda pc: 'ld c, h'),                           # 4c
	(0, lambda pc: 'ld c, l'),                           # 4d
	(0, lambda pc: 'ld c, [hl]'),                        # 4e
	(0, lambda pc: 'ld c, a'),                           # 4f
	(0, lambda pc: 'ld d, b'),                           # 50
	(0, lambda pc: 'ld d, c'),                           # 51
	(0, lambda pc: 'ld d, d'),                           # 52
	(0, lambda pc: 'ld d, e'),                           # 53
	(0, lambda pc: 'ld d, h'),                           # 54
	(0, lambda pc: 'ld d, l'),                           # 55
	(0, lambda pc: 'ld d, [hl]'),                        # 56
	(0, lambda pc: 'ld d, a'),                           # 57
	(0, lambda pc: 'ld e, b'),                           # 58
	(0, lambda pc: 'ld e, c'),                           # 59
	(0, lambda pc: 'ld e, d'),                           # 5a
	(0, lambda pc: 'ld e, e'),                           # 5b
	(0, lambda pc: 'ld e, h'),                           # 5c
	(0, lambda pc: 'ld e, l'),                           # 5d
	(0, lambda pc: 'ld e, [hl]'),                        # 5e
	(0, lambda pc: 'ld e, a'),                           # 5f
	(0, lambda pc: 'ld h, b'),                           # 60
	(0, lambda pc: 'ld h, c'),                           # 61
	(0, lambda pc: 'ld h, d'),                           # 62
	(0, lambda pc: 'ld h, e'),                           # 63
	(0, lambda pc: 'ld h, h'),                           # 64
	(0, lambda pc: 'ld h, l'),                           # 65
	(0, lambda pc: 'ld h, [hl]'),                        # 66
	(0, lambda pc: 'ld h, a'),                           # 67
	(0, lambda pc: 'ld l, b'),                           # 68
	(0, lambda pc: 'ld l, c'),                           # 69
	(0, lambda pc: 'ld l, d'),                           # 6a
	(0, lambda pc: 'ld l, e'),                           # 6b
	(0, lambda pc: 'ld l, h'),                           # 6c
	(0, lambda pc: 'ld l, l'),                           # 6d
	(0, lambda pc: 'ld l, [hl]'),                        # 6e
	(0, lambda pc: 'ld l, a'),                           # 6f
	(0, lambda pc: 'ld [hl], b'),                        # 70
	(0, lambda pc: 'ld [hl], c'),                        # 71
	(0, lambda pc: 'ld [hl], d'),                        # 72
	(0, lambda pc: 'ld [hl], e'),                        # 73
	(0, lambda pc: 'ld [hl], h'),                        # 74
	(0, lambda pc: 'ld [hl], l'),                        # 75
	(0, lambda pc: 'halt'),                              # 76
	(0, lambda pc: 'ld [hl], a'),                        # 77
	(0, lambda pc: 'ld a, b'),                           # 78
	(0, lambda pc: 'ld a, c'),                           # 79
	(0, lambda pc: 'ld a, d'),                           # 7a
	(0, lambda pc: 'ld a, e'),                           # 7b
	(0, lambda pc: 'ld a, h'),                           # 7c
	(0, lambda pc: 'ld a, l'),                           # 7d
	(0, lambda pc: 'ld a, [hl]'),                        # 7e
	(0, lambda pc: 'ld a, a'),                           # 7f
	(0, lambda pc: 'add b'),                             # 80
	(0, lambda pc: 'add c'),                             # 81
	(0, lambda pc: 'add d'),                             # 82
	(0, lambda pc: 'add e'),                             # 83
	(0, lambda pc: 'add h'),                             # 84
	(0, lambda pc: 'add l'),                             # 85
	(0, lambda pc: 'add [hl]'),                          # 86
	(0, lambda pc: 'add a'),                             # 87
	(0, lambda pc: 'adc b'),                             # 88
	(0, lambda pc: 'adc c'),                             # 89
	(0, lambda pc: 'adc d'),                             # 8a
	(0, lambda pc: 'adc e'),                             # 8b
	(0, lambda pc: 'adc h'),                             # 8c
	(0, lambda pc: 'adc l'),                             # 8d
	(0, lambda pc: 'adc [hl]'),                          # 8e
	(0, lambda pc: 'adc a'),                             # 8f
	(0, lambda pc: 'sub b'),                             # 90
	(0, lambda pc: 'sub c'),                             # 91
	(0, lambda pc: 'sub d'),                             # 92
	(0, lambda pc: 'sub e'),                             # 93
	(0, lambda pc: 'sub h'),                             # 94
	(0, lambda pc: 'sub l'),                             # 95
	(0, lambda pc: 'sub [hl]'),                          # 96
	(0, lambda pc: 'sub a'),                             # 97
	(0, lambda pc: 'sbc b'),                             # 98
	(0, lambda pc: 'sbc c'),                             # 99
	(0, lambda pc: 'sbc d'),                             # 9a
	(0, lambda pc: 'sbc e'),                             # 9b
	(0, lambda pc: 'sbc h'),                             # 9c
	(0, lambda pc: 'sbc l'),                             # 9d
	(0, lambda pc: 'sbc [hl]'),                          # 9e
	(0, lambda pc: 'sbc a'),                             # 9f
	(0, lambda pc: 'and b'),                             # a0
	(0, lambda pc: 'and c'),                             # a1
	(0, lambda pc: 'and d'),                             # a2
	(0, lambda pc: 'and e'),                             # a3
	(0, lambda pc: 'and h'),                             # a4
	(0, lambda pc: 'and l'),                             # a5
	(0, lambda pc: 'and [hl]'),                          # a6
	(0, lambda pc: 'and a'),                             # a7
	(0, lambda pc: 'xor b'),                             # a8
	(0, lambda pc: 'xor c'),                             # a9
	(0, lambda pc: 'xor d'),                             # aa
	(0, lambda pc: 'xor e'),                             # ab
	(0, lambda pc: 'xor h'),                             # ac
	(0, lambda pc: 'xor l'),                             # ad
	(0, lambda pc: 'xor [hl]'),                          # ae
	(0, lambda pc: 'xor a'),                             # af
	(0, lambda pc: 'or b'),                              # b0
	(0, lambda pc: 'or c'),                              # b1
	(0, lambda pc: 'or d'),                              # b2
	(0, lambda pc: 'or e'),                              # b3
	(0, lambda pc: 'or h'),                              # b4
	(0, lambda pc: 'or l'),                              # b5
	(0, lambda pc: 'or [hl]'),                           # b6
	(0, lambda pc: 'or a'),                              # b7
	(0, lambda pc: 'cp b'),                              # b8
	(0, lambda pc: 'cp c'),                              # b9
	(0, lambda pc: 'cp d'),                              # ba
	(0, lambda pc: 'cp e'),                              # bb
	(0, lambda pc: 'cp h'),                              # bc
	(0, lambda pc: 'cp l'),                              # bd
	(0, lambda pc: 'cp [hl]'),                           # be
	(0, lambda pc: 'cp a'),                              # bf
	(0, lambda pc: 'ret nz'),                            # c0
	(0, lambda pc: 'pop bc'),                            # c1
	(2, lambda pc, a, b: create_jp(pc, a, b, 'nz')),     # c2
	(2, create_jp),                                      # c3
	(2, lambda pc, a, b: create_call(pc, a, b, 'nz')),   # c4
	(0, lambda pc: 'push bc'),                           # c5
	(1, lambda pc, a: 'add %s' % u8(a)),                 # c6
	(0, lambda pc: 'rst $0'),                            # c7
	(0, lambda pc: 'ret z'),                             # c8
	(0, create_ret),                                     # c9
	(2, lambda pc, a, b: create_jp(pc, a, b, 'z')),      # ca
	(1, get_prefix_opcode),                              # cb
	(2, lambda pc, a, b: create_call(pc, a, b, 'z')),    # cc
	(2, lambda pc, a, b: create_call(pc, a, b)),         # cd
	(1, lambda pc, a: 'adc %s' % u8(a)),                 # ce
	(0, lambda pc: 'rst $8'),                            # cf
	(0, lambda pc: 'ret nc'),                            # d0
	(0, lambda pc: 'pop de'),                            # d1
	(2, lambda pc, a, b: create_jp(pc, a, b, 'nc')),     # d2
	(0, lambda pc: 'db $d3'),                            # d3
	(2, lambda pc, a, b: create_call(pc, a, b, 'nc')),   # d4
	(0, lambda pc: 'push de'),                           # d5
	(1, lambda pc, a: 'sub %s' % u8(a)),                 # d6
	(0, lambda pc: 'rst $10'),                           # d7
	(0, lambda pc: 'ret c'),                             # d8
	(0, lambda pc: 'reti'),                              # d9
	(2, lambda pc, a, b: create_jp(pc, a, b, 'c')),      # da
	(0, lambda pc: 'db $db'),                            # db
	(2, lambda pc, a, b: create_call(pc, a, b, 'c')),    # dc
	(0, lambda pc: 'db $dd'),                            # dd
	(1, lambda pc, a: 'sbc %s' % u8(a)),                 # de
	(0, lambda pc: 'rst $18'),                           # df
	(1, lambda pc, a: create_ldh(a, 'a')),               # e0
	(0, lambda pc: 'pop hl'),                            # e1
	(0, lambda pc: 'ld [$ff00+c], a'),                   # e2
	(0, lambda pc: 'db $e3'),                            # e3
	(0, lambda pc: 'db $e4'),                            # e4
	(0, lambda pc: 'push hl'),                           # e5
	(1, lambda pc, a: 'and %s' % u8(a)),                 # e6
	(0, lambda pc: 'rst $20'),                           # e7
	(1, lambda pc, a: 'add sp, %s' % s8(a, plus=False)), # e8
	(0, create_jp_hl),                                   # e9
	(2, lambda pc, a, b: 'ld [%s], a' % u16le(a, b)),    # ea
	(0, lambda pc: 'db $eb'),                            # eb
	(0, lambda pc: 'db $ec'),                            # ec
	(0, lambda pc: 'db $ed'),                            # ed
	(1, lambda pc, a: 'xor %s' % u8(a)),                 # ee
	(0, lambda pc: 'rst $28'),                           # ef
	(1, lambda pc, a: create_ldh('a', a)),               # f0
	(0, lambda pc: 'pop af'),                            # f1
	(0, lambda pc: 'ld a, [$ff00+c]'),                   # f2
	(0, lambda pc: 'di'),                                # f3
	(0, lambda pc: 'db $f4'),                            # f4
	(0, lambda pc: 'push af'),                           # f5
	(1, lambda pc, a: 'or %s' % u8(a)),                  # f6
	(0, lambda pc: 'rst $30'),                           # f7
	(1, lambda pc, a: 'ld hl, sp%s' % s8(a, plus=True)), # f8
	(0, lambda pc: 'ld sp, hl'),                         # f9
	(2, lambda pc, a, b: 'ld a, [%s]' % u16le(a, b)),    # fa
	(0, lambda pc: 'ei'),                                # fb
	(0, lambda pc: 'db $fc'),                            # fc
	(0, lambda pc: 'db $fd'),                            # fd
	(1, lambda pc, a: 'cp %s' % u8(a)),                  # fe
	(0, lambda pc: 'rst $38'),                           # ff
]


def disassemble(filename, entry_point=0x000000):
	global raw_data, data_size, starting_points, operations

	with open(filename, 'rb') as f:
		raw_data = dict(enumerate(f.read()))
		data_size = len(raw_data)

	starting_points.add(entry_point)

	while starting_points:
		pc = starting_points.pop()
		if pc in raw_data:
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

		elif pc in raw_data:
			chunk_pc = pc
			CHUNK_SIZE = 8
			data = []
			while pc in raw_data:
				data.append(raw_data[pc])
				pc += 1
			while data:
				chunk, data = data[:CHUNK_SIZE], data[CHUNK_SIZE:]
				operation = create_db(chunk_pc, *chunk)
				line = '%s%s' % (operation, ' ' * max(LINE_LENGTH - len(operation), 1))
				print('\t%s; %s-%s' % (line, format_address(chunk_pc), format_address(chunk_pc + len(chunk) - 1)))
				chunk_pc += CHUNK_SIZE
		
		else:
			pc += 1


def disassemble_from(pc):
	global raw_data, operations, terminate

	terminate = False

	while pc < data_size:
		if pc not in raw_data:
			return
		opcode = raw_data[pc]
		width, get_operation = opcode_table[opcode]

		if pc + width < data_size:
			args = [raw_data[pc + 1 + i] for i in range(width)]
			operations[pc] = (get_operation(pc, *args), [opcode] + args)
		else:
			bytes = [raw_data[a] for a in range(pc, data_size)]
			operations[pc] = (create_db(pc, *bytes), bytes)

		for i in range(pc, min(pc + 1 + width, data_size)):
			del raw_data[i]

		if terminate:
			return

		pc += 1 + width


def create_ldh(dest, src):
	if dest == 'a':
		return 'ld a, [%s]' % gbhw_register_table[src]
	if src == 'a':
		return 'ld [%s], a' % gbhw_register_table[dest]
	raise ValueError('ldh %s, %s' % (dest, src))

gbhw_register_table = [
	'rJOYP',     # 00
	'rSB',       # 01
	'rSC',       # 02
	'$ff03',     # 03
	'rDIV',      # 04
	'rTIMA',     # 05
	'rTMA',      # 06
	'rTAC',      # 07
	'$ff08',     # 08
	'$ff09',     # 09
	'$ff0a',     # 0a
	'$ff0b',     # 0b
	'$ff0c',     # 0c
	'$ff0d',     # 0d
	'$ff0e',     # 0e
	'rIF',       # 0f
	'rNR10',     # 10
	'rNR11',     # 11
	'rNR12',     # 12
	'rNR13',     # 13
	'rNR14',     # 14
	'rNR20',     # 15
	'rNR21',     # 16
	'rNR22',     # 17
	'rNR23',     # 18
	'rNR24',     # 19
	'rNR30',     # 1a
	'rNR31',     # 1b
	'rNR32',     # 1c
	'rNR33',     # 1d
	'rNR34',     # 1e
	'rNR40',     # 1f
	'rNR41',     # 20
	'rNR42',     # 21
	'rNR43',     # 22
	'rNR44',     # 23
	'rNR50',     # 24
	'rNR51',     # 25
	'rNR52',     # 26
	'$ff27',     # 27
	'$ff28',     # 28
	'$ff29',     # 29
	'$ff2a',     # 2a
	'$ff2b',     # 2b
	'$ff2c',     # 2c
	'$ff2d',     # 2d
	'$ff2e',     # 2e
	'$ff2f',     # 2f
	'rWave_0',   # 30
	'rWave_1',   # 31
	'rWave_2',   # 32
	'rWave_3',   # 33
	'rWave_4',   # 34
	'rWave_5',   # 35
	'rWave_6',   # 36
	'rWave_7',   # 37
	'rWave_8',   # 38
	'rWave_9',   # 39
	'rWave_a',   # 3a
	'rWave_b',   # 3b
	'rWave_c',   # 3c
	'rWave_d',   # 3d
	'rWave_e',   # 3e
	'rWave_f',   # 3f
	'rLCDC',     # 40
	'rSTAT',     # 41
	'rSCY',      # 42
	'rSCX',      # 43
	'rLY',       # 44
	'rLYC',      # 45
	'rDMA',      # 46
	'rBGP',      # 47
	'rOBP0',     # 48
	'rOBP1',     # 49
	'rWY',       # 4a
	'rWX',       # 4b
	'rLCDMODE',  # 4c
	'rKEY1',     # 4d
	'$ff4e',     # 4e
	'rVBK',      # 4f
	'rBLCK',     # 50
	'rHDMA1',    # 51
	'rHDMA2',    # 52
	'rHDMA3',    # 53
	'rHDMA4',    # 54
	'rHDMA5',    # 55
	'rRP',       # 56
	'$ff57',     # 57
	'$ff58',     # 58
	'$ff59',     # 59
	'$ff5a',     # 5a
	'$ff5b',     # 5b
	'$ff5c',     # 5c
	'$ff5d',     # 5d
	'$ff5e',     # 5e
	'$ff5f',     # 5f
	'$ff60',     # 60
	'$ff61',     # 61
	'$ff62',     # 62
	'$ff63',     # 63
	'$ff64',     # 64
	'$ff65',     # 65
	'$ff66',     # 66
	'$ff67',     # 67
	'rBGPI',     # 68
	'rBGPD',     # 69
	'rOBPI',     # 6a
	'rOBPD',     # 6b
	'rUNKNOWN1', # 6c
	'$ff6d',     # 6d
	'$ff6e',     # 6e
	'$ff6f',     # 6f
	'rSVBK',     # 70
	'$ff71',     # 71
	'rUNKNOWN2', # 72
	'rUNKNOWN3', # 73
	'rUNKNOWN4', # 74
	'rUNKNOWN5', # 75
	'rUNKNOWN6', # 76
	'rUNKNOWN7', # 77
	'$ff78',     # 78
	'$ff79',     # 79
	'$ff7a',     # 7a
	'$ff7b',     # 7b
	'$ff7c',     # 7c
	'$ff7d',     # 7d
	'$ff7e',     # 7e
	'$ff7f',     # 7f
	'$ff80',     # 80
	'$ff81',     # 81
	'$ff82',     # 82
	'$ff83',     # 83
	'$ff84',     # 84
	'$ff85',     # 85
	'$ff86',     # 86
	'$ff87',     # 87
	'$ff88',     # 88
	'$ff89',     # 89
	'$ff8a',     # 8a
	'$ff8b',     # 8b
	'$ff8c',     # 8c
	'$ff8d',     # 8d
	'$ff8e',     # 8e
	'$ff8f',     # 8f
	'$ff90',     # 90
	'$ff91',     # 91
	'$ff92',     # 92
	'$ff93',     # 93
	'$ff94',     # 94
	'$ff95',     # 95
	'$ff96',     # 96
	'$ff97',     # 97
	'$ff98',     # 98
	'$ff99',     # 99
	'$ff9a',     # 9a
	'$ff9b',     # 9b
	'$ff9c',     # 9c
	'$ff9d',     # 9d
	'$ff9e',     # 9e
	'$ff9f',     # 9f
	'$ffa0',     # a0
	'$ffa1',     # a1
	'$ffa2',     # a2
	'$ffa3',     # a3
	'$ffa4',     # a4
	'$ffa5',     # a5
	'$ffa6',     # a6
	'$ffa7',     # a7
	'$ffa8',     # a8
	'$ffa9',     # a9
	'$ffaa',     # aa
	'$ffab',     # ab
	'$ffac',     # ac
	'$ffad',     # ad
	'$ffae',     # ae
	'$ffaf',     # af
	'$ffb0',     # b0
	'$ffb1',     # b1
	'$ffb2',     # b2
	'$ffb3',     # b3
	'$ffb4',     # b4
	'$ffb5',     # b5
	'$ffb6',     # b6
	'$ffb7',     # b7
	'$ffb8',     # b8
	'$ffb9',     # b9
	'$ffba',     # ba
	'$ffbb',     # bb
	'$ffbc',     # bc
	'$ffbd',     # bd
	'$ffbe',     # be
	'$ffbf',     # bf
	'$ffc0',     # c0
	'$ffc1',     # c1
	'$ffc2',     # c2
	'$ffc3',     # c3
	'$ffc4',     # c4
	'$ffc5',     # c5
	'$ffc6',     # c6
	'$ffc7',     # c7
	'$ffc8',     # c8
	'$ffc9',     # c9
	'$ffca',     # ca
	'$ffcb',     # cb
	'$ffcc',     # cc
	'$ffcd',     # cd
	'$ffce',     # ce
	'$ffcf',     # cf
	'$ffd0',     # d0
	'$ffd1',     # d1
	'$ffd2',     # d2
	'$ffd3',     # d3
	'$ffd4',     # d4
	'$ffd5',     # d5
	'$ffd6',     # d6
	'$ffd7',     # d7
	'$ffd8',     # d8
	'$ffd9',     # d9
	'$ffda',     # da
	'$ffdb',     # db
	'$ffdc',     # dc
	'$ffdd',     # dd
	'$ffde',     # de
	'$ffdf',     # df
	'$ffe0',     # e0
	'$ffe1',     # e1
	'$ffe2',     # e2
	'$ffe3',     # e3
	'$ffe4',     # e4
	'$ffe5',     # e5
	'$ffe6',     # e6
	'$ffe7',     # e7
	'$ffe8',     # e8
	'$ffe9',     # e9
	'$ffea',     # ea
	'$ffeb',     # eb
	'$ffec',     # ec
	'$ffed',     # ed
	'$ffee',     # ee
	'$ffef',     # ef
	'$fff0',     # f0
	'$fff1',     # f1
	'$fff2',     # f2
	'$fff3',     # f3
	'$fff4',     # f4
	'$fff5',     # f5
	'$fff6',     # f6
	'$fff7',     # f7
	'$fff8',     # f8
	'$fff9',     # f9
	'$fffa',     # fa
	'$fffb',     # fb
	'$fffc',     # fc
	'$fffd',     # fd
	'$fffe',     # fe
	'rIE',       # ff
]


def main():
	global starting_points, labels
	if len(sys.argv) not in [2, 3]:
		print('Usage: %s a.bin [entry_point]', file=sys.stderr)
		sys.exit(1)
	try:
		entry_point = int(sys.argv[2], 16) if len(sys.argv) == 3 else 0
		labels[entry_point].add('ENTRY_POINT')
	except:
		print('Invalid entry point: %r', sys.argv[3], file=sys.stderr)
		sys.exit(1)
	disassemble(sys.argv[1], entry_point)

if __name__ == '__main__':
	main()
