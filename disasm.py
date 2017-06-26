#!/usr/bin/env python3

"""
Disassemble a GameBoy ROM into Z80 assembly code in rgbds syntax.
"""

__author__  = 'Rangi'
__version__ = '1.3'

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
	(1, lambda pc, a: create_ldh_to(a)),                 # e0
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
	(1, lambda pc, a: create_ldh_from(a)),               # f0
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


def create_ldh_to(a):
	return 'ld a, [%s]' % gbhw_register_table.get(a, u16le(a, 0xff))

def create_ldh_from(a):
	return 'ld [%s], a' % gbhw_register_table.get(a, u16le(a, 0xff))

gbhw_register_table = {
	0x00: 'rJOYP',
	0x01: 'rSB',
	0x02: 'rSC',
	0x04: 'rDIV',
	0x05: 'rTIMA',
	0x06: 'rTMA',
	0x07: 'rTAC',
	0x0f: 'rIF',
	0x10: 'rNR10',
	0x11: 'rNR11',
	0x12: 'rNR12',
	0x13: 'rNR13',
	0x14: 'rNR14',
	0x15: 'rNR20',
	0x16: 'rNR21',
	0x17: 'rNR22',
	0x18: 'rNR23',
	0x19: 'rNR24',
	0x1a: 'rNR30',
	0x1b: 'rNR31',
	0x1c: 'rNR32',
	0x1d: 'rNR33',
	0x1e: 'rNR34',
	0x1f: 'rNR40',
	0x20: 'rNR41',
	0x21: 'rNR42',
	0x22: 'rNR43',
	0x23: 'rNR44',
	0x24: 'rNR50',
	0x25: 'rNR51',
	0x26: 'rNR52',
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
	0x40: 'rLCDC',
	0x41: 'rSTAT',
	0x42: 'rSCY',
	0x43: 'rSCX',
	0x44: 'rLY',
	0x45: 'rLYC',
	0x46: 'rDMA',
	0x47: 'rBGP',
	0x48: 'rOBP0',
	0x49: 'rOBP1',
	0x4a: 'rWY',
	0x4b: 'rWX',
	0x4c: 'rLCDMODE',
	0x4d: 'rKEY1',
	0x4f: 'rVBK',
	0x50: 'rBLCK',
	0x51: 'rHDMA1',
	0x52: 'rHDMA2',
	0x53: 'rHDMA3',
	0x54: 'rHDMA4',
	0x55: 'rHDMA5',
	0x56: 'rRP',
	0x68: 'rBGPI',
	0x69: 'rBGPD',
	0x6a: 'rOBPI',
	0x6b: 'rOBPD',
	0x6c: 'rUNKNOWN1',
	0x70: 'rSVBK',
	0x72: 'rUNKNOWN2',
	0x73: 'rUNKNOWN3',
	0x74: 'rUNKNOWN4',
	0x75: 'rUNKNOWN5',
	0x76: 'rUNKNOWN6',
	0x77: 'rUNKNOWN7',
	0xff: 'rIE',
}


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
