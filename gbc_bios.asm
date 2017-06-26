; http://gbdev.gg8.se/wiki/articles/The_Cartridge_Header
; http://bgb.bircd.org/pandocs.htm#thecartridgeheader

; http://imrannazar.com/Gameboy-Z80-Opcode-Map
; http://pastraiser.com/cpu/gameboy/gameboy_opcodes.html
; http://gameboy.mongenel.com/dmg/opcodes.html
; http://gbdev.gg8.se/wiki/articles/CPU_Comparision_with_Z80

; https://realboyemulator.wordpress.com/2013/01/03/a-look-at-the-game-boy-bootstrap-let-the-fun-begin/
; https://www.emuparadise.me/biosfiles/bios.html

; https://hax.iimarckus.org/topic/7161/
; https://pastebin.com/1gqYntHg

ENTRY_POINT:
	ld sp, $fffe                                      ; 0000: 31 fe ff
	ld a, $2                                          ; 0003: 3e 02
	jp Function007c                                   ; 0005: c3 7c 00

Unknown_0008:
	db $d3, $00, $98, $a0, $12, $d3, $00, $80         ; 0008-000f
	db $00, $40, $1e, $53, $d0, $00, $1f, $42         ; 0010-0017
	db $1c, $00, $14, $2a, $4d, $19, $8c, $7e         ; 0018-001f
	db $00, $7c, $31, $6e, $4a, $45, $52, $4a         ; 0020-0027
	db $00, $00, $ff, $53, $1f, $7c, $ff, $03         ; 0028-002f
	db $1f, $00, $ff, $1f, $a7, $00, $ef, $1b         ; 0030-0037
	db $1f, $00, $ef, $1b, $00, $7c, $00, $00         ; 0038-003f
	db $ff, $03, $ce, $ed, $66, $66, $cc, $0d         ; 0040-0047
	db $00, $0b, $03, $73, $00, $83, $00, $0c         ; 0048-004f
	db $00, $0d, $00, $08, $11, $1f, $88, $89         ; 0050-0057
	db $00, $0e, $dc, $cc, $6e, $e6, $dd, $dd         ; 0058-005f
	db $d9, $99, $bb, $bb, $67, $63, $6e, $0e         ; 0060-0067
	db $ec, $cc, $dd, $dc, $99, $9f, $bb, $b9         ; 0068-006f
	db $33, $3e                                       ; 0070-0071

Unknown_0072:
	db $3c, $42, $b9, $a5, $b9, $a5                   ; 0072-0077
	db $42, $3c, $58, $43                             ; 0078-007b

Function007c:
	ld [rSVBK], a                                     ; 007c: e0 70
; a = the color number's mappings
	ld a, $fc                                         ; 007e: 3e fc
; initialize the palette
	ld [rBGP], a                                      ; 0080: e0 47
	call Function0275                                 ; 0082: cd 75 02
	call Function0200                                 ; 0085: cd 00 02
	ld h, $d0                                         ; 0088: 26 d0
	call Function0203                                 ; 008a: cd 03 02

	ld hl, $fe00                                      ; 008d: 21 00 fe
	ld c, 160                                         ; 0090: 0e a0
	xor a                                             ; 0092: af
.do_160:
	ld [hli], a                                       ; 0093: 22
	dec c                                             ; 0094: 0d
	jr nz, .do_160                                    ; 0095: 20 fc

; de = pointer to Nintendo logo in catrridge header
	ld de, $0104                                      ; 0097: 11 04 01
; hl = pointer to VRAM
	ld hl, $8010                                      ; 009a: 21 10 80
	ld c, h                                           ; 009d: 4c
.loop1:
; load next byte from Nintendo logo
	ld a, [de]                                        ; 009e: 1a
	ld [$ff00+c], a                                   ; 009f: e2
	inc c                                             ; 00a0: 0c
; decompress, scale and write pixels to VRAM (1)
	call Function03c6                                 ; 00a1: cd c6 03
; decompress, scale and write pixels to VRAM (2)
	call Function03c7                                 ; 00a4: cd c7 03
	inc de                                            ; 00a7: 13
	ld a, e                                           ; 00a8: 7b
	cp $34                                            ; 00a9: fe 34
; loop if not finished comparing
	jr nz, .loop1                                     ; 00ab: 20 f1

	ld de, Unknown_0072                               ; 00ad: 11 72 00
	ld b, 8                                           ; 00b0: 06 08
.do_8:
	ld a, [de]                                        ; 00b2: 1a
	inc de                                            ; 00b3: 13
	ld [hli], a                                       ; 00b4: 22
	inc hl                                            ; 00b5: 23
	dec b                                             ; 00b6: 05
	jr nz, .do_8                                      ; 00b7: 20 f9
	call Function03f0                                 ; 00b9: cd f0 03

	ld a, $01                                         ; 00bc: 3e 01
	ld [rVBK], a                                      ; 00be: e0 4f
	ld a, $91                                         ; 00c0: 3e 91
	ld [rLCDC], a                                     ; 00c2: e0 40
	ld hl, $98b2                                      ; 00c4: 21 b2 98
	ld b, $4e                                         ; 00c7: 06 4e
	ld c, $44                                         ; 00c9: 0e 44
	call Function0291                                 ; 00cb: cd 91 02
	xor a                                             ; 00ce: af
	ld [rVBK], a                                      ; 00cf: e0 4f

	ld c, $80                                         ; 00d1: 0e 80
	ld hl, $0042                                      ; 00d3: 21 42 00
	ld b, 24                                          ; 00d6: 06 18
.do_24:
	ld a, [$ff00+c]                                   ; 00d8: f2
	inc c                                             ; 00d9: 0c
	cp [hl]                                           ; 00da: be
.trap1:
	jr nz, .trap1                                     ; 00db: 20 fe
	inc hl                                            ; 00dd: 23
	dec b                                             ; 00de: 05
	jr nz, .do_24                                     ; 00df: 20 f7

	ld hl, $0134                                      ; 00e1: 21 34 01
	ld b, 25                                          ; 00e4: 06 19
	ld a, b                                           ; 00e6: 78
.do_25:
	add [hl]                                          ; 00e7: 86
	inc l                                             ; 00e8: 2c
	dec b                                             ; 00e9: 05
	jr nz, .do_25                                     ; 00ea: 20 fb
	add [hl]                                          ; 00ec: 86
.trap2:
	jr nz, .trap2                                     ; 00ed: 20 fe

	call Function031c                                 ; 00ef: cd 1c 03
	jr .skip_nops                                     ; 00f2: 18 02
	nop                                               ; 00f4
	nop                                               ; 00f5
.skip_nops:
	call Function05d0                                 ; 00f6: cd d0 05

	xor a                                             ; 00f9: af
	ld [rSVBK], a                                     ; 00fa: e0 70
	ld a, $11                                         ; 00fc: 3e 11
	ld [rBLCK], a                                     ; 00fe: e0 50

; The cartridge header is copied here, and begins with a boot procedure that
; will terminate this function, usually by jumping to the actual game code.
rept 256
	nop                                               ; 0100-01ff: 00
endr

Function0200:
	ld hl, $8000                                      ; 0200: 21 00 80
; fallthrough
Function0203:
	xor a                                             ; 0203: af
.loop:
	ld [hli], a                                       ; 0204: 22
	bit 5, h                                          ; 0205: cb 6c
	jr z, .loop                                       ; 0207: 28 fb
	ret                                               ; 0209: c9

Function020a:
	ld a, [hli]                                       ; 020a: 2a
	ld [de], a                                        ; 020b: 12
	inc de                                            ; 020c: 13
	dec c                                             ; 020d: 0d
	jr nz, Function020a                               ; 020e: 20 fa
	ret                                               ; 0210: c9

Function0211:
	push hl                                           ; 0211: e5
	ld hl, rIF                                        ; 0212: 21 0f ff
	res 0, [hl]                                       ; 0215: cb 86
.wait:
	bit 0, [hl]                                       ; 0217: cb 46
	jr z, .wait                                       ; 0219: 28 fc
	pop hl                                            ; 021b: e1
	ret                                               ; 021c: c9

Function021d:
	ld de, $ff00                                      ; 021d: 11 00 ff
	ld hl, $d003                                      ; 0220: 21 03 d0
	ld c, $0f                                         ; 0223: 0e 0f
	ld a, $30                                         ; 0225: 3e 30
	ld [de], a                                        ; 0227: 12
	ld a, $20                                         ; 0228: 3e 20
	ld [de], a                                        ; 022a: 12
	ld a, [de]                                        ; 022b: 1a
	cpl                                               ; 022c: 2f
	and c                                             ; 022d: a1
	swap a                                            ; 022e: cb 37
	ld b, a                                           ; 0230: 47
	ld a, $10                                         ; 0231: 3e 10
	ld [de], a                                        ; 0233: 12
	ld a, [de]                                        ; 0234: 1a
	cpl                                               ; 0235: 2f
	and c                                             ; 0236: a1
	or b                                              ; 0237: b0
	ld c, a                                           ; 0238: 4f
	ld a, [hl]                                        ; 0239: 7e
	xor c                                             ; 023a: a9
	and $f0                                           ; 023b: e6 f0
	ld b, a                                           ; 023d: 47
	ld a, [hli]                                       ; 023e: 2a
	xor c                                             ; 023f: a9
	and c                                             ; 0240: a1
	or b                                              ; 0241: b0
	ld [hld], a                                       ; 0242: 32
	ld b, a                                           ; 0243: 47
	ld a, c                                           ; 0244: 79
	ld [hl], a                                        ; 0245: 77
	ld a, $30                                         ; 0246: 3e 30
	ld [de], a                                        ; 0248: 12
	ret                                               ; 0249: c9

Function024a:
	ld a, $80                                         ; 024a: 3e 80
	ld [rBGPI], a                                     ; 024c: e0 68
	ld [rOBPI], a                                     ; 024e: e0 6a

	ld c, $6b                                         ; 0250: 0e 6b
.loop1:
	ld a, [hli]                                       ; 0252: 2a
	ld [$ff00+c], a                                   ; 0253: e2
	dec b                                             ; 0254: 05
	jr nz, .loop1                                     ; 0255: 20 fb
	ld c, d                                           ; 0257: 4a
	add hl, bc                                        ; 0258: 09

	ld b, e                                           ; 0259: 43
	ld c, $69                                         ; 025a: 0e 69
.loop2:
	ld a, [hli]                                       ; 025c: 2a
	ld [$ff00+c], a                                   ; 025d: e2
	dec b                                             ; 025e: 05
	jr nz, .loop2                                     ; 025f: 20 fb

	ret                                               ; 0261: c9

Function0262:
	push bc                                           ; 0262: c5
	push de                                           ; 0263: d5
	push hl                                           ; 0264: e5

	ld hl, $d800                                      ; 0265: 21 00 d8
	ld b, $01                                         ; 0268: 06 01
	ld d, $3f                                         ; 026a: 16 3f
	ld e, $40                                         ; 026c: 1e 40
	call Function024a                                 ; 026e: cd 4a 02

	pop hl                                            ; 0271: e1
	pop de                                            ; 0272: d1
	pop bc                                            ; 0273: c1
	ret                                               ; 0274: c9

Function0275:
	ld a, $80                                         ; 0275: 3e 80
	ld [rNR52], a                                     ; 0277: e0 26
	ld [rNR11], a                                     ; 0279: e0 11
	ld a, $f3                                         ; 027b: 3e f3
	ld [rNR12], a                                     ; 027d: e0 12
	ld [rNR51], a                                     ; 027f: e0 25
	ld a, $77                                         ; 0281: 3e 77
	ld [rNR50], a                                     ; 0283: e0 24
	ld hl, rWave_0                                    ; 0285: 21 30 ff
	xor a                                             ; 0288: af
	ld c, $10                                         ; 0289: 0e 10
Function028b:
	ld [hli], a                                       ; 028b: 22
	cpl                                               ; 028c: 2f
	dec c                                             ; 028d: 0d
	jr nz, Function028b                               ; 028e: 20 fb
	ret                                               ; 0290: c9

Function0291:
	call Function0211                                 ; 0291: cd 11 02
	call Function0262                                 ; 0294: cd 62 02
	ld a, c                                           ; 0297: 79
	cp $38                                            ; 0298: fe 38
	jr nz, Function02b0                               ; 029a: 20 14
	push hl                                           ; 029c: e5
	xor a                                             ; 029d: af
	ld [rVBK], a                                      ; 029e: e0 4f
	ld hl, $99a7                                      ; 02a0: 21 a7 99
	ld a, $38                                         ; 02a3: 3e 38
Function02a5:
	ld [hli], a                                       ; 02a5: 22
	inc a                                             ; 02a6: 3c
	cp $3f                                            ; 02a7: fe 3f
	jr nz, Function02a5                               ; 02a9: 20 fa
	ld a, $01                                         ; 02ab: 3e 01
	ld [rVBK], a                                      ; 02ad: e0 4f
	pop hl                                            ; 02af: e1
Function02b0:
	push bc                                           ; 02b0: c5
	push hl                                           ; 02b1: e5
	ld hl, $0143                                      ; 02b2: 21 43 01
	bit 7, [hl]                                       ; 02b5: cb 7e
	call z, Function0589                              ; 02b7: cc 89 05
	pop hl                                            ; 02ba: e1
	pop bc                                            ; 02bb: c1
	call Function0211                                 ; 02bc: cd 11 02
	ld a, c                                           ; 02bf: 79
	sub $30                                           ; 02c0: d6 30
	jp nc, Function0306                               ; 02c2: d2 06 03
	ld a, c                                           ; 02c5: 79
	cp $01                                            ; 02c6: fe 01
	jp z, Function0306                                ; 02c8: ca 06 03
	ld a, l                                           ; 02cb: 7d
	cp $d1                                            ; 02cc: fe d1
	jr z, Function02f1                                ; 02ce: 28 21
	push bc                                           ; 02d0: c5
	ld b, $03                                         ; 02d1: 06 03
Function02d3:
	ld c, $01                                         ; 02d3: 0e 01
Function02d5:
	ld d, $03                                         ; 02d5: 16 03
Function02d7:
	ld a, [hl]                                        ; 02d7: 7e
	and $f8                                           ; 02d8: e6 f8
	or c                                              ; 02da: b1
	ld [hli], a                                       ; 02db: 22
	dec d                                             ; 02dc: 15
	jr nz, Function02d7                               ; 02dd: 20 f8
	inc c                                             ; 02df: 0c
	ld a, c                                           ; 02e0: 79
	cp $06                                            ; 02e1: fe 06
	jr nz, Function02d5                               ; 02e3: 20 f0
	ld de, $11                                        ; 02e5: 11 11 00
	add hl, de                                        ; 02e8: 19
	dec b                                             ; 02e9: 05
	jr nz, Function02d3                               ; 02ea: 20 e7
	ld de, $ffa1                                      ; 02ec: 11 a1 ff
	add hl, de                                        ; 02ef: 19
	pop bc                                            ; 02f0: c1
Function02f1:
	inc b                                             ; 02f1: 04
	ld a, b                                           ; 02f2: 78
	ld e, $83                                         ; 02f3: 1e 83
	cp $62                                            ; 02f5: fe 62
	jr z, Function02ff                                ; 02f7: 28 06
	ld e, $c1                                         ; 02f9: 1e c1
	cp $64                                            ; 02fb: fe 64
	jr nz, Function0306                               ; 02fd: 20 07
Function02ff:
	ld a, e                                           ; 02ff: 7b
	ld [rNR13], a                                     ; 0300: e0 13
	ld a, $87                                         ; 0302: 3e 87
	ld [rNR14], a                                     ; 0304: e0 14
Function0306:
	ld a, [$d002]                                     ; 0306: fa 02 d0
	cp $00                                            ; 0309: fe 00
	jr z, Function0317                                ; 030b: 28 0a
	dec a                                             ; 030d: 3d
	ld [$d002], a                                     ; 030e: ea 02 d0
	ld a, c                                           ; 0311: 79
	cp $01                                            ; 0312: fe 01
	jp z, Function0291                                ; 0314: ca 91 02
Function0317:
	dec c                                             ; 0317: 0d
	jp nz, Function0291                               ; 0318: c2 91 02
	ret                                               ; 031b: c9

Function031c:
	ld c, $26                                         ; 031c: 0e 26
Function031e:
	call Function034a                                 ; 031e: cd 4a 03
	call Function0211                                 ; 0321: cd 11 02
	call Function0262                                 ; 0324: cd 62 02
	dec c                                             ; 0327: 0d
	jr nz, Function031e                               ; 0328: 20 f4
	call Function0211                                 ; 032a: cd 11 02
	ld a, $01                                         ; 032d: 3e 01
	ld [rVBK], a                                      ; 032f: e0 4f
	call Function033e                                 ; 0331: cd 3e 03
	call Function0341                                 ; 0334: cd 41 03
	xor a                                             ; 0337: af
	ld [rVBK], a                                      ; 0338: e0 4f
	call Function033e                                 ; 033a: cd 3e 03
	ret                                               ; 033d: c9

Function033e:
	ld hl, Unknown_0008                               ; 033e: 21 08 00
Function0341:
	ld de, $ff51                                      ; 0341: 11 51 ff
	ld c, $05                                         ; 0344: 0e 05
	call Function020a                                 ; 0346: cd 0a 02
	ret                                               ; 0349: c9

Function034a:
	push bc                                           ; 034a: c5
	push de                                           ; 034b: d5
	push hl                                           ; 034c: e5
	ld hl, $d840                                      ; 034d: 21 40 d8
	ld c, $20                                         ; 0350: 0e 20
Function0352:
	ld a, [hl]                                        ; 0352: 7e
	and $1f                                           ; 0353: e6 1f
	cp $1f                                            ; 0355: fe 1f
	jr z, Function035a                                ; 0357: 28 01
	inc a                                             ; 0359: 3c
Function035a:
	ld d, a                                           ; 035a: 57
	ld a, [hli]                                       ; 035b: 2a
	rlc a                                             ; 035c: 07
	rlc a                                             ; 035d: 07
	rlc a                                             ; 035e: 07
	and $07                                           ; 035f: e6 07
	ld b, a                                           ; 0361: 47
	ld a, [hld]                                       ; 0362: 3a
	rlc a                                             ; 0363: 07
	rlc a                                             ; 0364: 07
	rlc a                                             ; 0365: 07
	and $18                                           ; 0366: e6 18
	or b                                              ; 0368: b0
	cp $1f                                            ; 0369: fe 1f
	jr z, Function036e                                ; 036b: 28 01
	inc a                                             ; 036d: 3c
Function036e:
	rrc a                                             ; 036e: 0f
	rrc a                                             ; 036f: 0f
	rrc a                                             ; 0370: 0f
	ld b, a                                           ; 0371: 47
	and $e0                                           ; 0372: e6 e0
	or d                                              ; 0374: b2
	ld [hli], a                                       ; 0375: 22
	ld a, b                                           ; 0376: 78
	and $03                                           ; 0377: e6 03
	ld e, a                                           ; 0379: 5f
	ld a, [hl]                                        ; 037a: 7e
	rrc a                                             ; 037b: 0f
	rrc a                                             ; 037c: 0f
	and $1f                                           ; 037d: e6 1f
	cp $1f                                            ; 037f: fe 1f
	jr z, Function0384                                ; 0381: 28 01
	inc a                                             ; 0383: 3c
Function0384:
	rlc a                                             ; 0384: 07
	rlc a                                             ; 0385: 07
	or e                                              ; 0386: b3
	ld [hli], a                                       ; 0387: 22
	dec c                                             ; 0388: 0d
	jr nz, Function0352                               ; 0389: 20 c7
	pop hl                                            ; 038b: e1
	pop de                                            ; 038c: d1
	pop bc                                            ; 038d: c1
	ret                                               ; 038e: c9

Function038f:
	ld c, $00                                         ; 038f: 0e 00
.loop:
	ld a, [de]                                        ; 0391: 1a
	and $f0                                           ; 0392: e6 f0
	bit 1, c                                          ; 0394: cb 49
	jr z, .skip1                                      ; 0396: 28 02
	swap a                                            ; 0398: cb 37
.skip1:
	ld b, a                                           ; 039a: 47
	inc hl                                            ; 039b: 23
	ld a, [hl]                                        ; 039c: 7e
	or b                                              ; 039d: b0
	ld [hli], a                                       ; 039e: 22
	ld a, [de]                                        ; 039f: 1a
	and $0f                                           ; 03a0: e6 0f
	bit 1, c                                          ; 03a2: cb 49
	jr nz, .skip2                                     ; 03a4: 20 02
	swap a                                            ; 03a6: cb 37
.skip2:
	ld b, a                                           ; 03a8: 47
	inc hl                                            ; 03a9: 23
	ld a, [hl]                                        ; 03aa: 7e
	or b                                              ; 03ab: b0
	ld [hli], a                                       ; 03ac: 22
	inc de                                            ; 03ad: 13
	bit 0, c                                          ; 03ae: cb 41
	jr z, .skip3                                      ; 03b0: 28 0d
	push de                                           ; 03b2: d5
	ld de, -8                                         ; 03b3: 11 f8 ff
	bit 1, c                                          ; 03b6: cb 49
	jr z, .negative                                   ; 03b8: 28 03
	ld de, 8                                          ; 03ba: 11 08 00
.negative:
	add hl, de                                        ; 03bd: 19
	pop de                                            ; 03be: d1
.skip3:
	inc c                                             ; 03bf: 0c
	ld a, c                                           ; 03c0: 79
	cp $18                                            ; 03c1: fe 18
	jr nz, .loop                                      ; 03c3: 20 cc
	ret                                               ; 03c5: c9

Function03c6:
	ld b, a                                           ; 03c6: 47
Function03c7:
	push de                                           ; 03c7: d5
	ld d, $04                                         ; 03c8: 16 04
.loop:
	ld e, b                                           ; 03ca: 58
	rl b                                              ; 03cb: cb 10
	rla                                               ; 03cd: 17
	rl e                                              ; 03ce: cb 13
	rla                                               ; 03d0: 17
	dec d                                             ; 03d1: 15
	jr nz, .loop                                      ; 03d2: 20 f6
	pop de                                            ; 03d4: d1
	ld [hli], a                                       ; 03d5: 22
	inc hl                                            ; 03d6: 23
	ld [hli], a                                       ; 03d7: 22
	inc hl                                            ; 03d8: 23
	ret                                               ; 03d9: c9

Function03da:
	ld a, $19                                         ; 03da: 3e 19
	ld [$9910], a                                     ; 03dc: ea 10 99
	ld hl, $992f                                      ; 03df: 21 2f 99
Function03e2:
	ld c, $0c                                         ; 03e2: 0e 0c
Function03e4:
	dec a                                             ; 03e4: 3d
	jr z, .done                                       ; 03e5: 28 08
	ld [hld], a                                       ; 03e7: 32
	dec c                                             ; 03e8: 0d
	jr nz, Function03e4                               ; 03e9: 20 f9
	ld l, $0f                                         ; 03eb: 2e 0f
	jr Function03e2                                   ; 03ed: 18 f3
.done:
	ret                                               ; 03ef: c9

Function03f0:
	ld a, $01                                         ; 03f0: 3e 01
	ld [rVBK], a                                      ; 03f2: e0 4f
	call Function0200                                 ; 03f4: cd 00 02
	ld de, Unknown_0607                               ; 03f7: 11 07 06
	ld hl, $8080                                      ; 03fa: 21 80 80
	ld c, $c0                                         ; 03fd: 0e c0
Function03ff:
	ld a, [de]                                        ; 03ff: 1a
	ld [hli], a                                       ; 0400: 22
	inc hl                                            ; 0401: 23
	ld [hli], a                                       ; 0402: 22
	inc hl                                            ; 0403: 23
	inc de                                            ; 0404: 13
	dec c                                             ; 0405: 0d
	jr nz, Function03ff                               ; 0406: 20 f7
	ld de, $0104                                      ; 0408: 11 04 01
	call Function038f                                 ; 040b: cd 8f 03
	ld bc, $ffa8                                      ; 040e: 01 a8 ff
	add hl, bc                                        ; 0411: 09
	call Function038f                                 ; 0412: cd 8f 03
	ld bc, $fff8                                      ; 0415: 01 f8 ff
	add hl, bc                                        ; 0418: 09
	ld de, $0072                                      ; 0419: 11 72 00
	ld c, $08                                         ; 041c: 0e 08
Function041e:
	inc hl                                            ; 041e: 23
	ld a, [de]                                        ; 041f: 1a
	ld [hli], a                                       ; 0420: 22
	inc de                                            ; 0421: 13
	dec c                                             ; 0422: 0d
	jr nz, Function041e                               ; 0423: 20 f9
	ld hl, $98c2                                      ; 0425: 21 c2 98
	ld b, $08                                         ; 0428: 06 08
	ld a, $08                                         ; 042a: 3e 08
Function042c:
	ld c, $10                                         ; 042c: 0e 10
Function042e:
	ld [hli], a                                       ; 042e: 22
	dec c                                             ; 042f: 0d
	jr nz, Function042e                               ; 0430: 20 fc
	ld de, $0010                                      ; 0432: 11 10 00
	add hl, de                                        ; 0435: 19
	dec b                                             ; 0436: 05
	jr nz, Function042c                               ; 0437: 20 f3
	xor a                                             ; 0439: af
	ld [rVBK], a                                      ; 043a: e0 4f
	ld hl, $98c2                                      ; 043c: 21 c2 98
	ld a, $08                                         ; 043f: 3e 08
Function0441:
	ld [hli], a                                       ; 0441: 22
	inc a                                             ; 0442: 3c
	cp $18                                            ; 0443: fe 18
	jr nz, Function0449                               ; 0445: 20 02
	ld l, $e2                                         ; 0447: 2e e2
Function0449:
	cp $28                                            ; 0449: fe 28
	jr nz, Function0450                               ; 044b: 20 03
	ld hl, $9902                                      ; 044d: 21 02 99
Function0450:
	cp $38                                            ; 0450: fe 38
	jr nz, Function0441                               ; 0452: 20 ed
	ld hl, $08d8                                      ; 0454: 21 d8 08
	ld de, $d840                                      ; 0457: 11 40 d8
	ld b, $08                                         ; 045a: 06 08
Function045c:
	ld a, $ff                                         ; 045c: 3e ff
	ld [de], a                                        ; 045e: 12
	inc de                                            ; 045f: 13
	ld [de], a                                        ; 0460: 12
	inc de                                            ; 0461: 13
	ld c, $02                                         ; 0462: 0e 02
	call Function020a                                 ; 0464: cd 0a 02
	ld a, $00                                         ; 0467: 3e 00
	ld [de], a                                        ; 0469: 12
	inc de                                            ; 046a: 13
	ld [de], a                                        ; 046b: 12
	inc de                                            ; 046c: 13
	inc de                                            ; 046d: 13
	inc de                                            ; 046e: 13
	dec b                                             ; 046f: 05
	jr nz, Function045c                               ; 0470: 20 ea
	call Function0262                                 ; 0472: cd 62 02
	ld hl, $014b                                      ; 0475: 21 4b 01
	ld a, [hl]                                        ; 0478: 7e
	cp $33                                            ; 0479: fe 33
	jr nz, Function0488                               ; 047b: 20 0b
	ld l, $44                                         ; 047d: 2e 44
	ld e, $30                                         ; 047f: 1e 30
	ld a, [hli]                                       ; 0481: 2a
	cp e                                              ; 0482: bb
	jr nz, Function04ce                               ; 0483: 20 49
	inc e                                             ; 0485: 1c
	jr Function048c                                   ; 0486: 18 04

Function0488:
	ld l, $4b                                         ; 0488: 2e 4b
	ld e, $01                                         ; 048a: 1e 01
Function048c:
	ld a, [hli]                                       ; 048c: 2a
	cp e                                              ; 048d: bb
	jr nz, Function04ce                               ; 048e: 20 3e
	ld l, $34                                         ; 0490: 2e 34
	ld bc, $0010                                      ; 0492: 01 10 00
Function0495:
	ld a, [hli]                                       ; 0495: 2a
	add b                                             ; 0496: 80
	ld b, a                                           ; 0497: 47
	dec c                                             ; 0498: 0d
	jr nz, Function0495                               ; 0499: 20 fa
	ld [$d000], a                                     ; 049b: ea 00 d0
	ld hl, $06c7                                      ; 049e: 21 c7 06
	ld c, $00                                         ; 04a1: 0e 00
Function04a3:
	ld a, [hli]                                       ; 04a3: 2a
	cp b                                              ; 04a4: b8
	jr z, Function04af                                ; 04a5: 28 08
	inc c                                             ; 04a7: 0c
	ld a, c                                           ; 04a8: 79
	cp $4f                                            ; 04a9: fe 4f
	jr nz, Function04a3                               ; 04ab: 20 f6
	jr Function04ce                                   ; 04ad: 18 1f

Function04af:
	ld a, c                                           ; 04af: 79
	sub $41                                           ; 04b0: d6 41
	jr c, Function04d0                                ; 04b2: 38 1c
	ld hl, $0716                                      ; 04b4: 21 16 07
	ld d, $00                                         ; 04b7: 16 00
	ld e, a                                           ; 04b9: 5f
	add hl, de                                        ; 04ba: 19
Function04bb:
	ld a, [$0137]                                     ; 04bb: fa 37 01
	ld d, a                                           ; 04be: 57
	ld a, [hl]                                        ; 04bf: 7e
	cp d                                              ; 04c0: ba
	jr z, Function04d0                                ; 04c1: 28 0d
	ld de, $000e                                      ; 04c3: 11 0e 00
	add hl, de                                        ; 04c6: 19
	ld a, c                                           ; 04c7: 79
	add e                                             ; 04c8: 83
	ld c, a                                           ; 04c9: 4f
	sub $5e                                           ; 04ca: d6 5e
	jr c, Function04bb                                ; 04cc: 38 ed
Function04ce:
	ld c, $00                                         ; 04ce: 0e 00
Function04d0:
	ld hl, $0733                                      ; 04d0: 21 33 07
	ld b, $00                                         ; 04d3: 06 00
	add hl, bc                                        ; 04d5: 09
	ld a, [hl]                                        ; 04d6: 7e
	and $1f                                           ; 04d7: e6 1f
	ld [$d008], a                                     ; 04d9: ea 08 d0
	ld a, [hl]                                        ; 04dc: 7e
	and $e0                                           ; 04dd: e6 e0
	rlc a                                             ; 04df: 07
	rlc a                                             ; 04e0: 07
	rlc a                                             ; 04e1: 07
	ld [$d00b], a                                     ; 04e2: ea 0b d0
	call Function04e9                                 ; 04e5: cd e9 04
	ret                                               ; 04e8: c9

Function04e9:
	ld de, $0791                                      ; 04e9: 11 91 07
	ld hl, $d900                                      ; 04ec: 21 00 d9
	ld a, [$d00b]                                     ; 04ef: fa 0b d0
	ld b, a                                           ; 04f2: 47
	ld c, $1e                                         ; 04f3: 0e 1e
Function04f5:
	bit 0, b                                          ; 04f5: cb 40
	jr nz, Function04fb                               ; 04f7: 20 02
	inc de                                            ; 04f9: 13
	inc de                                            ; 04fa: 13
Function04fb:
	ld a, [de]                                        ; 04fb: 1a
	ld [hli], a                                       ; 04fc: 22
	jr nz, Function0501                               ; 04fd: 20 02
	dec de                                            ; 04ff: 1b
	dec de                                            ; 0500: 1b
Function0501:
	bit 1, b                                          ; 0501: cb 48
	jr nz, Function0507                               ; 0503: 20 02
	inc de                                            ; 0505: 13
	inc de                                            ; 0506: 13
Function0507:
	ld a, [de]                                        ; 0507: 1a
	ld [hli], a                                       ; 0508: 22
	inc de                                            ; 0509: 13
	inc de                                            ; 050a: 13
	jr nz, Function050f                               ; 050b: 20 02
	dec de                                            ; 050d: 1b
	dec de                                            ; 050e: 1b
Function050f:
	bit 2, b                                          ; 050f: cb 50
	jr z, Function0518                                ; 0511: 28 05
	dec de                                            ; 0513: 1b
	dec hl                                            ; 0514: 2b
	ld a, [de]                                        ; 0515: 1a
	ld [hli], a                                       ; 0516: 22
	inc de                                            ; 0517: 13
Function0518:
	ld a, [de]                                        ; 0518: 1a
	ld [hli], a                                       ; 0519: 22
	inc de                                            ; 051a: 13
	dec c                                             ; 051b: 0d
	jr nz, Function04f5                               ; 051c: 20 d7
	ld hl, $d900                                      ; 051e: 21 00 d9
	ld de, $da00                                      ; 0521: 11 00 da
	call Function0564                                 ; 0524: cd 64 05
	ret                                               ; 0527: c9

Function0528:
	ld hl, $0012                                      ; 0528: 21 12 00
	ld a, [$d005]                                     ; 052b: fa 05 d0
	rlc a                                             ; 052e: 07
	rlc a                                             ; 052f: 07
	ld b, $00                                         ; 0530: 06 00
	ld c, a                                           ; 0532: 4f
	add hl, bc                                        ; 0533: 09
	ld de, $d840                                      ; 0534: 11 40 d8
	ld b, $08                                         ; 0537: 06 08
Function0539:
	push hl                                           ; 0539: e5
	ld c, $02                                         ; 053a: 0e 02
	call Function020a                                 ; 053c: cd 0a 02
	inc de                                            ; 053f: 13
	inc de                                            ; 0540: 13
	inc de                                            ; 0541: 13
	inc de                                            ; 0542: 13
	inc de                                            ; 0543: 13
	inc de                                            ; 0544: 13
	pop hl                                            ; 0545: e1
	dec b                                             ; 0546: 05
	jr nz, Function0539                               ; 0547: 20 f0
	ld de, $d842                                      ; 0549: 11 42 d8
	ld c, $02                                         ; 054c: 0e 02
	call Function020a                                 ; 054e: cd 0a 02
	ld de, $d84a                                      ; 0551: 11 4a d8
	ld c, $02                                         ; 0554: 0e 02
	call Function020a                                 ; 0556: cd 0a 02
	dec hl                                            ; 0559: 2b
	dec hl                                            ; 055a: 2b
	ld de, $d844                                      ; 055b: 11 44 d8
	ld c, $02                                         ; 055e: 0e 02
	call Function020a                                 ; 0560: cd 0a 02
	ret                                               ; 0563: c9

Function0564:
	ld c, $60                                         ; 0564: 0e 60
.loop:
	ld a, [hli]                                       ; 0566: 2a
	push hl                                           ; 0567: e5
	push bc                                           ; 0568: c5
	ld hl, $07e8                                      ; 0569: 21 e8 07
	ld b, $00                                         ; 056c: 06 00
	ld c, a                                           ; 056e: 4f
	add hl, bc                                        ; 056f: 09
	ld c, $08                                         ; 0570: 0e 08
	call Function020a                                 ; 0572: cd 0a 02
	pop bc                                            ; 0575: c1
	pop hl                                            ; 0576: e1
	dec c                                             ; 0577: 0d
	jr nz, .loop                                      ; 0578: 20 ec
	ret                                               ; 057a: c9

Function057b:
	ld a, [$d008]                                     ; 057b: fa 08 d0
	ld de, $0018                                      ; 057e: 11 18 00
	inc a                                             ; 0581: 3c
Function0582:
	dec a                                             ; 0582: 3d
	jr z, .done                                       ; 0583: 28 03
	add hl, de                                        ; 0585: 19
	jr nz, Function0582                               ; 0586: 20 fa
.done:
	ret                                               ; 0588: c9

Function0589:
	call Function021d                                 ; 0589: cd 1d 02
	ld a, b                                           ; 058c: 78
	and $ff                                           ; 058d: e6 ff
	jr z, .skip                                       ; 058f: 28 0f
	ld hl, $08e4                                      ; 0591: 21 e4 08
	ld b, $00                                         ; 0594: 06 00
.loop:
	ld a, [hli]                                       ; 0596: 2a
	cp c                                              ; 0597: b9
	jr z, .continue                                   ; 0598: 28 08
	inc b                                             ; 059a: 04
	ld a, b                                           ; 059b: 78
	cp $0c                                            ; 059c: fe 0c
	jr nz, .loop                                      ; 059e: 20 f6
.skip:
	jr .done                                          ; 05a0: 18 2d

.continue:
	ld a, b                                           ; 05a2: 78
	ld [$d005], a                                     ; 05a3: ea 05 d0
	ld a, $1e                                         ; 05a6: 3e 1e
	ld [$d002], a                                     ; 05a8: ea 02 d0
	ld de, $000b                                      ; 05ab: 11 0b 00
	add hl, de                                        ; 05ae: 19
	ld d, [hl]                                        ; 05af: 56
	ld a, d                                           ; 05b0: 7a
	and $1f                                           ; 05b1: e6 1f
	ld e, a                                           ; 05b3: 5f
	ld hl, $d008                                      ; 05b4: 21 08 d0
	ld a, [hld]                                       ; 05b7: 3a
	ld [hli], a                                       ; 05b8: 22
	ld a, e                                           ; 05b9: 7b
	ld [hl], a                                        ; 05ba: 77
	ld a, d                                           ; 05bb: 7a
	and $e0                                           ; 05bc: e6 e0
	rlc a                                             ; 05be: 07
	rlc a                                             ; 05bf: 07
	rlc a                                             ; 05c0: 07
	ld e, a                                           ; 05c1: 5f
	ld hl, $d00b                                      ; 05c2: 21 0b d0
	ld a, [hld]                                       ; 05c5: 3a
	ld [hli], a                                       ; 05c6: 22
	ld a, e                                           ; 05c7: 7b
	ld [hl], a                                        ; 05c8: 77
	call Function04e9                                 ; 05c9: cd e9 04
	call Function0528                                 ; 05cc: cd 28 05
.done:
	ret                                               ; 05cf: c9

Function05d0:
	call Function0211                                 ; 05d0: cd 11 02
	ld a, [$0143]                                     ; 05d3: fa 43 01
	bit 7, a                                          ; 05d6: cb 7f
	jr z, .ok                                         ; 05d8: 28 04
	ld [rLCDMODE], a                                  ; 05da: e0 4c
	jr .done                                          ; 05dc: 18 28
.ok:
	ld a, $04                                         ; 05de: 3e 04
	ld [rLCDMODE], a                                  ; 05e0: e0 4c
	ld a, $01                                         ; 05e2: 3e 01
	ld [rUNKNOWN1], a                                 ; 05e4: e0 6c
	ld hl, $da00                                      ; 05e6: 21 00 da
	call Function057b                                 ; 05e9: cd 7b 05
	ld b, $10                                         ; 05ec: 06 10
	ld d, $00                                         ; 05ee: 16 00
	ld e, $08                                         ; 05f0: 1e 08
	call Function024a                                 ; 05f2: cd 4a 02
	ld hl, $007a                                      ; 05f5: 21 7a 00
	ld a, [$d000]                                     ; 05f8: fa 00 d0
	ld b, a                                           ; 05fb: 47
	ld c, $02                                         ; 05fc: 0e 02
.loop:
	ld a, [hli]                                       ; 05fe: 2a
	cp b                                              ; 05ff: b8
	call z, Function03da                              ; 0600: cc da 03
	dec c                                             ; 0603: 0d
	jr nz, .loop                                      ; 0604: 20 f8
.done:
	ret                                               ; 0606: c9

Unknown_0607:
	db $01, $0f, $3f, $7e, $ff, $ff, $c0, $00         ; 0607-060e
	db $c0, $f0, $f1, $03, $7c, $fc, $fe, $fe         ; 060f-0616
	db $03, $07, $07, $0f, $e0, $e0, $f0, $f0         ; 0617-061e
	db $1e, $3e, $7e, $fe, $0f, $0f, $1f, $1f         ; 061f-0626
	db $ff, $ff, $00, $00, $01, $01, $01, $03         ; 0627-062e
	db $ff, $ff, $e1, $e0, $c0, $f0, $f9, $fb         ; 062f-0636
	db $1f, $7f, $f8, $e0, $f3, $fd, $3e, $1e         ; 0637-063e
	db $e0, $f0, $f9, $7f, $3e, $7c, $f8, $e0         ; 063f-0646
	db $f8, $f0, $f0, $f8, $00, $00, $7f, $7f         ; 0647-064e
	db $07, $0f, $9f, $bf, $9e, $1f, $ff, $ff         ; 064f-0656
	db $0f, $1e, $3e, $3c, $f1, $fb, $7f, $7f         ; 0657-065e
	db $fe, $de, $df, $9f, $1f, $3f, $3e, $3c         ; 065f-0666
	db $f8, $f8, $00, $00, $03, $03, $07, $07         ; 0667-066e
	db $ff, $ff, $c1, $c0, $f3, $e7, $f7, $f3         ; 066f-0676
	db $c0, $c0, $c0, $c0, $1f, $1f, $1e, $3e         ; 0677-067e
	db $3f, $1f, $3e, $3e, $80, $00, $00, $00         ; 067f-0686
	db $7c, $1f, $07, $00, $0f, $ff, $fe, $00         ; 0687-068e
	db $7c, $f8, $f0, $00, $1f, $0f, $0f, $00         ; 068f-0696
	db $7c, $f8, $f8, $00, $3f, $3e, $1c, $00         ; 0697-069e
	db $0f, $0f, $0f, $00, $7c, $ff, $ff, $00         ; 069f-06a6
	db $00, $f8, $f8, $00, $07, $0f, $0f, $00         ; 06a7-06ae
	db $81, $ff, $ff, $00, $f3, $e1, $80, $00         ; 06af-06b6
	db $e0, $ff, $7f, $00, $fc, $f0, $c0, $00         ; 06b7-06be
	db $3e, $7c, $7c, $00, $00, $00, $00, $00         ; 06bf-06c6
	db $00, $88, $16, $36, $d1, $db, $f2, $3c         ; 06c7-06ce
	db $8c, $92, $3d, $5c, $58, $c9, $3e, $70         ; 06cf-06d6
	db $1d, $59, $69, $19, $35, $a8, $14, $aa         ; 06d7-06de
	db $75, $95, $99, $34, $6f, $15, $ff, $97         ; 06df-06e6
	db $4b, $90, $17, $10, $39, $f7, $f6, $a2         ; 06e7-06ee
	db $49, $4e, $43, $68, $e0, $8b, $f0, $ce         ; 06ef-06f6
	db $0c, $29, $e8, $b7, $86, $9a, $52, $01         ; 06f7-06fe
	db $9d, $71, $9c, $bd, $5d, $6d, $67, $3f         ; 06ff-0706
	db $6b, $b3, $46, $28, $a5, $c6, $d3, $27         ; 0707-070e
	db $61, $18, $66, $6a, $bf, $0d, $f4, $42         ; 070f-0716
	db $45, $46, $41, $41, $52, $42, $45, $4b         ; 0717-071e
	db $45, $4b, $20, $52, $2d, $55, $52, $41         ; 071f-0726
	db $52, $20, $49, $4e, $41, $49, $4c, $49         ; 0727-072e
	db $43, $45, $20, $52, $7c, $08, $12, $a3         ; 072f-0736
	db $a2, $07, $87, $4b, $20, $12, $65, $a8         ; 0737-073e
	db $16, $a9, $86, $b1, $68, $a0, $87, $66         ; 073f-0746
	db $12, $a1, $30, $3c, $12, $85, $12, $64         ; 0747-074e
	db $1b, $07, $06, $6f, $6e, $6e, $ae, $af         ; 074f-0756
	db $6f, $b2, $af, $b2, $a8, $ab, $6f, $af         ; 0757-075e
	db $86, $ae, $a2, $a2, $12, $af, $13, $12         ; 075f-0766
	db $a1, $6e, $af, $af, $ad, $06, $4c, $6e         ; 0767-076e
	db $af, $af, $12, $7c, $ac, $a8, $6a, $6e         ; 076f-0776
	db $13, $a0, $2d, $a8, $2b, $ac, $64, $ac         ; 0777-077e
	db $6d, $87, $bc, $60, $b4, $13, $72, $7c         ; 077f-0786
	db $b5, $ae, $ae, $7c, $7c, $65, $a2, $6c         ; 0787-078e
	db $64, $85, $80, $b0, $40, $88, $20, $68         ; 078f-0796
	db $de, $00, $70, $de, $20, $78, $20, $20         ; 0797-079e
	db $38, $20, $b0, $90, $20, $b0, $a0, $e0         ; 079f-07a6
	db $b0, $c0, $98, $b6, $48, $80, $e0, $50         ; 07a7-07ae
	db $1e, $1e, $58, $20, $b8, $e0, $88, $b0         ; 07af-07b6
	db $10, $20, $00, $10, $20, $e0, $18, $e0         ; 07b7-07be
	db $18, $00, $18, $e0, $20, $a8, $e0, $20         ; 07bf-07c6
	db $18, $e0, $00, $20, $18, $d8, $c8, $18         ; 07c7-07ce
	db $e0, $00, $e0, $40, $28, $28, $28, $18         ; 07cf-07d6
	db $e0, $60, $20, $18, $e0, $00, $00, $08         ; 07d7-07de
	db $e0, $18, $30, $d0, $d0, $d0, $20, $e0         ; 07df-07e6
	db $e8, $ff, $7f, $bf, $32, $d0, $00, $00         ; 07e7-07ee
	db $00, $9f, $63, $79, $42, $b0, $15, $cb         ; 07ef-07f6
	db $04, $ff, $7f, $31, $6e, $4a, $45, $00         ; 07f7-07fe
	db $00, $ff, $7f, $ef, $1b, $00, $02, $00         ; 07ff-0806
	db $00, $ff, $7f, $1f, $42, $f2, $1c, $00         ; 0807-080e
	db $00, $ff, $7f, $94, $52, $4a, $29, $00         ; 080f-0816
	db $00, $ff, $7f, $ff, $03, $2f, $01, $00         ; 0817-081e
	db $00, $ff, $7f, $ef, $03, $d6, $01, $00         ; 081f-0826
	db $00, $ff, $7f, $b5, $42, $c8, $3d, $00         ; 0827-082e
	db $00, $74, $7e, $ff, $03, $80, $01, $00         ; 082f-0836
	db $00, $ff, $67, $ac, $77, $13, $1a, $6b         ; 0837-083e
	db $2d, $d6, $7e, $ff, $4b, $75, $21, $00         ; 083f-0846
	db $00, $ff, $53, $5f, $4a, $52, $7e, $00         ; 0847-084e
	db $00, $ff, $4f, $d2, $7e, $4c, $3a, $e0         ; 084f-0856
	db $1c, $ed, $03, $ff, $7f, $5f, $25, $00         ; 0857-085e
	db $00, $6a, $03, $1f, $02, $ff, $03, $ff         ; 085f-0866
	db $7f, $ff, $7f, $df, $01, $12, $01, $00         ; 0867-086e
	db $00, $1f, $23, $5f, $03, $f2, $00, $09         ; 086f-0876
	db $00, $ff, $7f, $ea, $03, $1f, $01, $00         ; 0877-087e
	db $00, $9f, $29, $1a, $00, $0c, $00, $00         ; 087f-0886
	db $00, $ff, $7f, $7f, $02, $1f, $00, $00         ; 0887-088e
	db $00, $ff, $7f, $e0, $03, $06, $02, $20         ; 088f-0896
	db $01, $ff, $7f, $eb, $7e, $1f, $00, $00         ; 0897-089e
	db $7c, $ff, $7f, $ff, $3f, $00, $7e, $1f         ; 089f-08a6
	db $00, $ff, $7f, $ff, $03, $1f, $00, $00         ; 08a7-08ae
	db $00, $ff, $03, $1f, $00, $0c, $00, $00         ; 08af-08b6
	db $00, $ff, $7f, $3f, $03, $93, $01, $00         ; 08b7-08be
	db $00, $00, $00, $00, $42, $7f, $03, $ff         ; 08bf-08c6
	db $7f, $ff, $7f, $8c, $7e, $00, $7c, $00         ; 08c7-08ce
	db $00, $ff, $7f, $ef, $1b, $80, $61, $00         ; 08cf-08d6
	db $00, $ff, $7f, $00, $7c, $e0, $03, $1f         ; 08d7-08de
	db $7c, $1f, $00, $ff, $03, $40, $41, $42         ; 08df-08e6
	db $20, $21, $22, $80, $81, $82, $10, $11         ; 08e7-08ee
	db $12, $12, $b0, $79, $b8, $ad, $16, $17         ; 08ef-08f6
	db $07, $ba, $05, $7c, $13, $00, $00, $00         ; 08f7-08fe
	db $00                                            ; 08ff-08ff
