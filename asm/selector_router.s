; Draft 65816 router for the fourth mode-selector entry.
; NOT linked into the ROM and NOT a playable patch yet.
;
; Expected hook (exact French Ultime Menace ROM):
;   file offset 0x1FAB18: A9 05 8D 78 18
; Replace only after the new StoryInit/StoryFrame and relocated state tables
; are complete and tested:
;   22 4E 98 BE EA   ; JSL $BE:984E ; NOP
;
; Planned placement (LoROM bank BE, only if the candidate range is proven safe):
;   init pointer table:  BE:9806 (file 0x1F1806, 12 x 3-byte pointers)
;   frame pointer table: BE:982A (file 0x1F182A, 12 x 3-byte pointers)
;   selector router:     BE:984E
;   StoryInit:           BE:986A
;   StoryFrame:          BE:986B
;
; The router preserves the processor status and leaves choices 0-2 on their
; original path. Choice 3 selects new global state 11. The caller's existing
; cleanup and dispatcher jump then run as before.
;
; Before enabling this source:
; - verify the screen label/tilemap for the fourth option;
; - prove the candidate ROM range is not referenced by any data/resource;
; - allocate story flags only after a WRAM audit;
; - implement and test StoryInit/StoryFrame;
; - build and test the complete patch in an emulator.

.setcpu "65816"

.export StorySelectorRouter

.segment "STORYCODE"

StorySelectorRouter:
    php
    rep #$20
    lda $196C
    cmp #$0003
    beq @story_choice

    ; Preserve the original behavior for cursor values 0, 1, and 2.
    sep #$20
    lda #$05
    sta $1878
    plp
    rtl

@story_choice:
    ; Global state 11 is added by the relocated init/frame pointer tables.
    sep #$20
    lda #$0B
    sta $20
    plp
    rtl
