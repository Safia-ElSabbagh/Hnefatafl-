import pygame
import sys
import copy
import math
import threading
import time
import Hnefatafl

# ═══════════════════════════════════════════════════════════════════════════════
#  COLOUR HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def C(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2],16) for i in (0,2,4))

def blend(c1, c2, t):
    return tuple(max(0,min(255,int(c1[i]+(c2[i]-c1[i])*t))) for i in range(3))

# ── Palette ──────────────────────────────────────────────────────────────────
BG         = C("1a1108")
PANEL_BG   = C("221608")
CELL_DARK  = C("4a2c12")
CELL_LIGHT = C("7a4e28")
GRID_LINE  = C("2e1a08")
BORDER_C   = C("8b6030")
ACCENT     = C("d4a843")
ACCENT2    = C("f0c060")
THRONE_COL = C("3d1f6e")
CORNER_COL = C("7a0000")
ATT_BODY   = C("c0392b")
ATT_RIM    = C("7b241c")
ATT_SHINE  = C("e74c3c")
DEF_BODY   = C("d5d0c0")
DEF_RIM    = C("8a8070")
DEF_SHINE  = C("ecf0f1")
KING_BODY  = C("f0c040")
KING_RIM   = C("b8860b")
KING_SHINE = C("fde68a")
TEXT_C     = C("e8d5a0")
TEXT_DIM   = C("7a6540")
TEXT_ATT   = C("e74c3c")
TEXT_DEF   = C("c8c0a8")
SEL_RING   = C("ffe066")
MOVE_DOT   = C("d4a843")
LAST_RING  = C("80ee80")

# ── Layout ────────────────────────────────────────────────────────────────────
CELL_SZ  = 58
BOARD_PAD = 50
PANEL_W  = 195
BOARD_X  = PANEL_W + 10
BOARD_Y  = 40
WIN_W    = BOARD_X + BOARD_PAD*2 + Hnefatafl.boardsize*CELL_SZ + PANEL_W + 10
WIN_H    = BOARD_Y + BOARD_PAD*2 + Hnefatafl.boardsize*CELL_SZ + 40
FPS      = 60

# ═══════════════════════════════════════════════════════════════════════════════
#  DRAWING
# ═══════════════════════════════════════════════════════════════════════════════

def cell_rect(r, c):
    x = BOARD_X + BOARD_PAD + c*CELL_SZ
    y = BOARD_Y + BOARD_PAD + r*CELL_SZ
    return pygame.Rect(x, y, CELL_SZ, CELL_SZ)

def cell_center(r, c):
    rect = cell_rect(r,c)
    return rect.centerx, rect.centery

def px(c): return BOARD_X + BOARD_PAD + c*CELL_SZ + CELL_SZ//2
def py(r): return BOARD_Y + BOARD_PAD + r*CELL_SZ + CELL_SZ//2

def draw_piece(surf, piece, cx, cy, R, selected=False, last=False):
    # Drop shadow
    sh = pygame.Surface((R*2+12, R*2+12), pygame.SRCALPHA)
    pygame.draw.circle(sh, (0,0,0,90), (R+6, R+8), R)
    surf.blit(sh, (cx-R-6, cy-R-4))

    if piece=='A':   body,rim,shine = ATT_BODY, ATT_RIM, ATT_SHINE
    elif piece=='D': body,rim,shine = DEF_BODY, DEF_RIM, DEF_SHINE
    elif piece=='K': body,rim,shine = KING_BODY, KING_RIM, KING_SHINE
    else: return

    if selected:
        glow = pygame.Surface((R*2+20, R*2+20), pygame.SRCALPHA)
        for i in range(6, 0, -1):
            pygame.draw.circle(glow, (*SEL_RING, i*18), (R+10,R+10), R+i*2)
        surf.blit(glow, (cx-R-10, cy-R-10))
        pygame.draw.circle(surf, SEL_RING, (cx,cy), R+5, 3)
    elif last:
        pygame.draw.circle(surf, LAST_RING, (cx,cy), R+5, 2)

    pygame.draw.circle(surf, rim, (cx,cy), R)
    pygame.draw.circle(surf, body, (cx,cy), R-3)
    # Shine
    pygame.draw.circle(surf, shine, (cx-R//4, cy-R//4), R//3)

    # Icon drawn with lines/polys
    sw = R//2
    if piece == 'A':
        pygame.draw.line(surf, ATT_RIM, (cx-sw,cy-sw), (cx+sw,cy+sw), 3)
        pygame.draw.line(surf, ATT_RIM, (cx+sw,cy-sw), (cx-sw,cy+sw), 3)
        pygame.draw.line(surf, (230,120,100), (cx-sw+1,cy-sw+1), (cx+sw-1,cy+sw-1), 1)
        pygame.draw.line(surf, (230,120,100), (cx+sw-1,cy-sw+1), (cx-sw+1,cy+sw-1), 1)
    elif piece == 'D':
        pts = [(cx,cy-sw),(cx+sw,cy-sw//3),(cx+sw//2,cy+sw),(cx-sw//2,cy+sw),(cx-sw,cy-sw//3)]
        pygame.draw.polygon(surf, DEF_RIM, pts)
        pygame.draw.polygon(surf, DEF_SHINE, pts, 2)
        pygame.draw.line(surf, DEF_RIM, (cx,cy-sw), (cx,cy+sw//2), 1)
    elif piece == 'K':
        pts = [(cx-sw,cy+sw//2),(cx-sw,cy),(cx-sw//2,cy-sw//2),(cx,cy-sw),
               (cx+sw//2,cy-sw//2),(cx+sw,cy),(cx+sw,cy+sw//2)]
        pygame.draw.polygon(surf, KING_RIM, pts)
        pygame.draw.polygon(surf, ACCENT2, pts, 2)

def draw_board(surf, fonts, game_state, selected, valid_moves, last_move, anim_t):
    # Board outer glow
    br = pygame.Rect(BOARD_X+BOARD_PAD-10, BOARD_Y+BOARD_PAD-10,
                     Hnefatafl.boardsize*CELL_SZ+20, Hnefatafl.boardsize*CELL_SZ+20)
    game_state2 = pygame.Surface((br.width+10, br.height+10), pygame.SRCALPHA)
    pygame.draw.rect(game_state2, (0,0,0,130), (0,0,br.width+10,br.height+10), border_radius=8)
    surf.blit(game_state2, (br.x-5, br.y-5))

    # Double border
    r1 = pygame.Rect(BOARD_X+BOARD_PAD-5, BOARD_Y+BOARD_PAD-5, Hnefatafl.boardsize*CELL_SZ+10, Hnefatafl.boardsize*CELL_SZ+10)
    r2 = pygame.Rect(BOARD_X+BOARD_PAD-9, BOARD_Y+BOARD_PAD-9, Hnefatafl.boardsize*CELL_SZ+18, Hnefatafl.boardsize*CELL_SZ+18)
    pygame.draw.rect(surf, BORDER_C, r1, 2, border_radius=3)
    pygame.draw.rect(surf, ACCENT,   r2, 2, border_radius=4)

    # Cells
    for r in range(Hnefatafl.boardsize):
        for c in range(Hnefatafl.boardsize):
            rect = cell_rect(r,c)
            color = CELL_LIGHT if (r+c)%2==0 else CELL_DARK
            pygame.draw.rect(surf, color, rect)
            pygame.draw.rect(surf, GRID_LINE, rect, 1)

    # Last move highlight
    if last_move:
        for pos in last_move:
            rrr,ccc = pos
            rect = cell_rect(rrr,ccc)
            hs = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            pygame.draw.rect(hs, (*LAST_RING, 40), (0,0,rect.w,rect.h))
            surf.blit(hs, rect.topleft)
            pygame.draw.rect(surf, LAST_RING, rect, 2)

    # Selected highlight
    if selected:
        rrr,ccc = selected
        rect = cell_rect(rrr,ccc)
        hs = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        pygame.draw.rect(hs, (*SEL_RING, 55), (0,0,rect.w,rect.h))
        surf.blit(hs, rect.topleft)
        pygame.draw.rect(surf, SEL_RING, rect, 3)

    # Corner squares
    for rrr,ccc in Hnefatafl.corner_positions:
        rect = cell_rect(rrr,ccc)
        pygame.draw.rect(surf, CORNER_COL, rect)
        pygame.draw.rect(surf, blend(CORNER_COL,(255,255,255),0.3), rect, 2)
        lbl = fonts['sm'].render("X", True, (255,200,200))
        surf.blit(lbl, lbl.get_rect(center=rect.center))

    # Throne
    rrr,ccc = Hnefatafl.throne_position
    if game_state["board"][rrr][ccc] != 'K':
        rect = cell_rect(rrr,ccc)
        pygame.draw.rect(surf, THRONE_COL, rect)
        pygame.draw.rect(surf, blend(THRONE_COL,(255,255,255),0.35), rect, 2)
        lbl = fonts['sm'].render("T", True, (200,180,255))
        surf.blit(lbl, lbl.get_rect(center=rect.center))

    # Grid labels
    for i in range(Hnefatafl.boardsize):
        col_lbl = fonts['tiny'].render(chr(ord('A')+i), True, TEXT_DIM)
        cx2 = BOARD_X+BOARD_PAD+i*CELL_SZ+CELL_SZ//2
        surf.blit(col_lbl, col_lbl.get_rect(center=(cx2, BOARD_Y+BOARD_PAD//2)))
        surf.blit(col_lbl, col_lbl.get_rect(center=(cx2, BOARD_Y+BOARD_PAD+Hnefatafl.boardsize*CELL_SZ+BOARD_PAD//2)))
        row_lbl = fonts['tiny'].render(str(i), True, TEXT_DIM)
        cy2 = BOARD_Y+BOARD_PAD+i*CELL_SZ+CELL_SZ//2
        surf.blit(row_lbl, row_lbl.get_rect(center=(BOARD_X+BOARD_PAD//2, cy2)))
        surf.blit(row_lbl, row_lbl.get_rect(center=(BOARD_X+BOARD_PAD+Hnefatafl.boardsize*CELL_SZ+BOARD_PAD//2, cy2)))

    # Move dots (animated)
    dot_r = 9 + int(math.sin(anim_t*4)*2)
    for _,(mr,mc) in valid_moves:
        ccx,ccy = cell_center(mr,mc)
        ds = pygame.Surface((dot_r*2+6, dot_r*2+6), pygame.SRCALPHA)
        pygame.draw.circle(ds, (*MOVE_DOT, 200), (dot_r+3, dot_r+3), dot_r)
        pygame.draw.circle(ds, (*ACCENT2, 255), (dot_r+3, dot_r+3), dot_r, 2)
        surf.blit(ds, (ccx-dot_r-3, ccy-dot_r-3))

    # Pieces
    board = game_state["board"]
    for r in range(Hnefatafl.boardsize):
        for c in range(Hnefatafl.boardsize):
            cell = board[r][c]
            if cell in ('A','D','K'):
                ccx,ccy = cell_center(r,c)
                R = CELL_SZ//2 - 5
                sel = selected==(r,c)
                lm = last_move is not None and (r,c) in last_move
                draw_piece(surf, cell, ccx, ccy, R, sel, lm)

def draw_left_panel(surf, fonts, game_state, human_side, difficulty):
    pygame.draw.rect(surf, PANEL_BG, (0, 0, PANEL_W, WIN_H))
    pygame.draw.line(surf, BORDER_C, (PANEL_W-1,0), (PANEL_W-1,WIN_H), 2)

    y = 16
    def label(txt, col, fnt='tiny'):
        nonlocal y
        lbl = fonts[fnt].render(txt, True, col)
        surf.blit(lbl, (12, y))
        y += lbl.get_height() + 2

    def divider():
        nonlocal y
        pygame.draw.line(surf, BORDER_C, (12,y), (PANEL_W-12,y), 1)
        y += 10

    # Runes header
    label("ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃ", TEXT_DIM, 'tiny')
    divider()

    label("YOUR SIDE", TEXT_DIM, 'tiny')
    label(human_side.upper(), ACCENT, 'md')
    divider()

    label("DIFFICULTY", TEXT_DIM, 'tiny')
    dcol = {"easy":(80,200,80),"medium":ACCENT,"hard":(220,80,80)}.get(difficulty, TEXT_C)
    label(difficulty.upper(), dcol, 'md')
    divider()

    label("CAPTURED", TEXT_DIM, 'tiny')
    label(f"Attackers:  {game_state['captured_attackers']}", TEXT_ATT, 'sm')
    label(f"Defenders:  {game_state['captured_defenders']}", TEXT_DEF, 'sm')
    divider()

    label("LEGEND", TEXT_DIM, 'tiny')
    legend = [
        (ATT_BODY, "Attacker"),
        (DEF_BODY, "Defender"),
        (KING_BODY, "King"),
        (THRONE_COL, "Throne"),
        (CORNER_COL, "Escape corner"),
    ]
    for col, name in legend:
        pygame.draw.circle(surf, col, (22, y+8), 7)
        pygame.draw.circle(surf, blend(col,(0,0,0),0.4), (22,y+8), 7, 1)
        lbl = fonts['tiny'].render(name, True, TEXT_C)
        surf.blit(lbl, (36, y+1))
        y += 20
    divider()

    label("ᛇᛈᛉᛊᛏᛒᛖᛗᛚᛜᛞᛟ", TEXT_DIM, 'tiny')

def draw_right_panel(surf, fonts, game_state, human_side, thinking, anim_t):
    rx = BOARD_X + BOARD_PAD*2 + Hnefatafl.boardsize*CELL_SZ + 10
    pygame.draw.rect(surf, PANEL_BG, (rx, 0, PANEL_W, WIN_H))
    pygame.draw.line(surf, BORDER_C, (rx, 0), (rx, WIN_H), 2)

    y = 16; px2 = rx + 12

    def label(txt, col, fnt='tiny'):
        nonlocal y
        lbl = fonts[fnt].render(txt, True, col)
        surf.blit(lbl, (px2, y))
        y += lbl.get_height() + 3

    def divider():
        nonlocal y
        pygame.draw.line(surf, BORDER_C, (px2,y), (px2+PANEL_W-24,y), 1)
        y += 10

    label("ᛁᛃᛇᛈᛉᛊᛏᛒᛖᛗᛚᛜ", TEXT_DIM, 'tiny')
    divider()
    label("CURRENT TURN", TEXT_DIM, 'tiny')

    if game_state["game_over"]:
        label("GAME OVER", ACCENT, 'md')
        label(f"{game_state['winner'].upper()} WINS", ACCENT2, 'sm')
    else:
        turn = game_state["turn"]
        is_human = (turn == human_side)
        col = TEXT_ATT if turn=="attacker" else TEXT_DEF
        label("YOUR TURN" if is_human else "CPU TURN", col, 'md')
        label(turn.capitalize(), col, 'sm')
        if thinking:
            dots = "." * (int(anim_t*2)%4)
            label(f"Thinking{dots}", TEXT_DIM, 'tiny')

    divider()
    label("HOW TO PLAY", TEXT_DIM, 'tiny')
    tips = [
        "Click a piece to",
        "  select it",
        "Click a gold dot",
        "  to move there",
        "Rook-style moves",
        "  (straight lines)",
        "Sandwich enemies",
        "  to capture them",
        "Defenders: King",
        "  escapes to corner",
        "Attackers: surround",
        "  the King",
        "",
        "N = New game",
        "ESC = Menu",
    ]
    for tip in tips:
        lbl = fonts['tiny'].render(tip, True, TEXT_DIM)
        surf.blit(lbl, (px2, y)); y += 15

    divider()
    label("ᛟᛞᛚᛜᛒᛏᛊᛉᛈᛇᛃᛁ", TEXT_DIM, 'tiny')

def draw_title(surf, fonts):
    title = fonts['md'].render("  HNEFATAFL  —  THE VIKING GAME  ", True, ACCENT)
    surf.blit(title, title.get_rect(center=(WIN_W//2, BOARD_Y//2 + 4)))

def draw_status(surf, fonts, msg):
    y = WIN_H - 34
    pygame.draw.rect(surf, PANEL_BG, (0, y, WIN_W, 34))
    pygame.draw.line(surf, BORDER_C, (0,y), (WIN_W,y), 1)
    lbl = fonts['sm'].render(msg, True, TEXT_C)
    surf.blit(lbl, lbl.get_rect(midleft=(PANEL_W+20, y+17)))

def draw_gameover(surf, fonts, winner, human_side):
    ov = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
    pygame.draw.rect(ov, (0,0,0,150), (0,0,WIN_W,WIN_H))
    surf.blit(ov, (0,0))
    bw,bh = 440,190; bx=(WIN_W-bw)//2; by=(WIN_H-bh)//2
    pygame.draw.rect(surf, PANEL_BG, (bx,by,bw,bh), border_radius=12)
    pygame.draw.rect(surf, ACCENT,   (bx,by,bw,bh), 3, border_radius=12)
    is_win = (winner == human_side)
    main_txt = "VICTORY!" if is_win else "DEFEAT!"
    col = ACCENT2 if is_win else (220,80,80)
    tl = fonts['lg'].render(main_txt, True, col)
    surf.blit(tl, tl.get_rect(center=(WIN_W//2, by+55)))
    sub = fonts['md'].render(f"{winner.upper()} WINS THE BATTLE", True, TEXT_C)
    surf.blit(sub, sub.get_rect(center=(WIN_W//2, by+95)))
    hint = fonts['sm'].render("Press N for New Game   |   ESC for Menu", True, TEXT_DIM)
    surf.blit(hint, hint.get_rect(center=(WIN_W//2, by+148)))

# ═══════════════════════════════════════════════════════════════════════════════
#  MENU
# ═══════════════════════════════════════════════════════════════════════════════

class Btn:
    def __init__(self, rect, text, base_col, text_col, font, selected=False):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.base_col = base_col
        self.text_col = text_col
        self.font = font
        self.selected = selected

    def draw(self, surf):
        mp = pygame.mouse.get_pos()
        hovered = self.rect.collidepoint(mp)
        col = blend(self.base_col, (255,255,255), 0.2) if hovered else self.base_col
        if self.selected:
            pygame.draw.rect(surf, ACCENT, self.rect.inflate(6,6), border_radius=7)
        pygame.draw.rect(surf, col, self.rect, border_radius=5)
        pygame.draw.rect(surf, BORDER_C, self.rect, 1, border_radius=5)
        lbl = self.font.render(self.text, True, self.text_col)
        surf.blit(lbl, lbl.get_rect(center=self.rect.center))

    def clicked(self, event):
        return event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and self.rect.collidepoint(event.pos)

def run_menu(screen, fonts, clock):
    side = ["attacker"]
    diff = ["medium"]

    def make_btns():
        bx = (WIN_W-460)//2; by = (WIN_H-400)//2
        btns = {}
        btns['att'] = Btn((bx+20,by+128,200,42),"Attacker (Black)",
            blend(ATT_RIM,PANEL_BG,0.4), TEXT_ATT, fonts['sm'], side[0]=="attacker")
        btns['def'] = Btn((bx+240,by+128,200,42),"Defender (White)",
            blend(DEF_RIM,PANEL_BG,0.4), TEXT_DEF, fonts['sm'], side[0]=="defender")
        btns['easy'] = Btn((bx+20,by+238,130,40),"Easy",
            blend((50,180,80),PANEL_BG,0.5),(80,220,100),fonts['sm'],diff[0]=="easy")
        btns['medium'] = Btn((bx+165,by+238,130,40),"Medium",
            blend(ACCENT,PANEL_BG,0.5),ACCENT,fonts['sm'],diff[0]=="medium")
        btns['hard'] = Btn((bx+310,by+238,130,40),"Hard",
            blend((200,60,60),PANEL_BG,0.5),(220,80,80),fonts['sm'],diff[0]=="hard")
        btns['start'] = Btn((bx+130,by+322,200,52),"START GAME",
            blend(ACCENT,PANEL_BG,0.3),(20,14,4),fonts['md'])
        return btns

    btns = make_btns()
    anim_t = 0.0

    runes = "ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃᛇᛈᛉᛊᛏᛒᛖᛗᛚᛜᛞᛟ"

    while True:
        dt = clock.tick(FPS)/1000.0
        anim_t += dt

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()

            if btns['att'].clicked(ev): side[0]="attacker"; btns=make_btns()
            if btns['def'].clicked(ev): side[0]="defender"; btns=make_btns()
            if btns['easy'].clicked(ev): diff[0]="easy"; btns=make_btns()
            if btns['medium'].clicked(ev): diff[0]="medium"; btns=make_btns()
            if btns['hard'].clicked(ev): diff[0]="hard"; btns=make_btns()
            if btns['start'].clicked(ev):
                return side[0], diff[0]

        screen.fill(BG)

        # Animated rune rain
        for i in range(18):
            x = (i*173+71) % WIN_W
            y = int((anim_t*25 + i*90) % WIN_H)
            rl = fonts['tiny'].render(runes[i%len(runes)], True, (*TEXT_DIM, 50))
            screen.blit(rl, (x, y))

        bx = (WIN_W-460)//2; by = (WIN_H-400)//2
        bw,bh = 460,400

        # Box shadow
        sh = pygame.Surface((bw+16,bh+16), pygame.SRCALPHA)
        pygame.draw.rect(sh, (0,0,0,120), (0,0,bw+16,bh+16), border_radius=14)
        screen.blit(sh, (bx-8, by-8))

        # Main box
        pygame.draw.rect(screen, PANEL_BG, (bx,by,bw,bh), border_radius=12)
        pygame.draw.rect(screen, ACCENT,   (bx,by,bw,bh), 2, border_radius=12)
        pygame.draw.rect(screen, BORDER_C, (bx+4,by+4,bw-8,bh-8), 1, border_radius=10)

        title = fonts['xl'].render("HNEFATAFL", True, ACCENT)
        screen.blit(title, title.get_rect(center=(WIN_W//2, by+40)))
        sub = fonts['sm'].render("The Ancient Viking Strategy Game", True, TEXT_DIM)
        screen.blit(sub, sub.get_rect(center=(WIN_W//2, by+72)))
        pygame.draw.line(screen, BORDER_C, (bx+24,by+92), (bx+bw-24,by+92), 1)

        sl = fonts['sm'].render("CHOOSE YOUR SIDE", True, TEXT_DIM)
        screen.blit(sl, sl.get_rect(center=(WIN_W//2, by+110)))
        dl = fonts['sm'].render("DIFFICULTY", True, TEXT_DIM)
        screen.blit(dl, dl.get_rect(center=(WIN_W//2, by+216)))

        for btn in btns.values(): btn.draw(screen)

        # Corner runes
        for txt,ax,ay in [("ᚠᚢᚦ",bx+14,by+14),("ᛟᛞᛚ",bx+bw-56,by+14),
                           ("ᛁᛃᛇ",bx+14,by+bh-22),("ᛏᛒᛖ",bx+bw-56,by+bh-22)]:
            rl = fonts['tiny'].render(txt, True, TEXT_DIM)
            screen.blit(rl, (ax,ay))

        pygame.display.flip()

# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Hnefatafl — Viking Chess")

    # Window icon
    ico = pygame.Surface((32,32), pygame.SRCALPHA)
    pygame.draw.circle(ico, KING_BODY, (16,16), 13)
    pygame.draw.circle(ico, KING_RIM,  (16,16), 13, 2)
    pygame.display.set_icon(ico)

    clock = pygame.time.Clock()

    def load_font(size, bold=False):
        for name in ["Georgia","Times New Roman","DejaVu Serif","Palatino","serif",None]:
            try:
                if name: return pygame.font.SysFont(name, size, bold=bold)
                else:    return pygame.font.Font(None, size+4)
            except: continue
        return pygame.font.Font(None, size+4)

    fonts = {
        'xl':   load_font(30, True),
        'lg':   load_font(24, True),
        'md':   load_font(19, True),
        'sm':   load_font(15),
        'tiny': load_font(12),
    }

    while True:   # outer loop allows "New Game" to restart
        # ── Menu ──
        human_side, difficulty = run_menu(screen, fonts, clock)

        # ── Game ──
        game_state = Hnefatafl.make_initial_state()
        selected    = None
        valid_moves = []
        last_move   = None
        thinking    = False
        status_msg  = f"You play as {human_side.upper()}. Good luck, Viking!"
        anim_t      = 0.0
        game_over_shown = False

        computer_result = [None]   # thread writes here

        def do_computer_turn():
            nonlocal thinking, status_msg
            thinking = True
            status_msg = "Computer is thinking..."
            def t():
                m = Hnefatafl.get_computer_move(game_state, difficulty)
                computer_result[0] = m
            threading.Thread(target=t, daemon=True).start()

        # If human chose defender, computer (attacker) goes first
        if human_side == "defender":
            do_computer_turn()

        running = True
        restart  = False

        while running:
            dt = clock.tick(FPS)/1000.0
            anim_t += dt

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        running = False  # back to menu
                    if ev.key == pygame.K_n:
                        running = False; restart = True

                # Human click
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button==1:
                    if not thinking and not game_state["game_over"]:
                        if game_state["turn"] == human_side:
                            mx,my = ev.pos
                            bx2 = BOARD_X+BOARD_PAD; by2 = BOARD_Y+BOARD_PAD
                            cc = (mx-bx2)//CELL_SZ; rr = (my-by2)//CELL_SZ
                            if 0<=rr<Hnefatafl.boardsize and 0<=cc<Hnefatafl.boardsize:
                                board = game_state["board"]; cell = board[rr][cc]
                                if selected:
                                    mt = next((to for fr,to in valid_moves if to==(rr,cc)),None)
                                    if mt:
                                        Hnefatafl.move_piece(game_state, selected, mt)
                                        Hnefatafl.detect_capture(game_state, mt)
                                        Hnefatafl.win_condition(game_state)
                                        last_move = (selected, mt)
                                        selected=None; valid_moves=[]
                                        if not game_state["game_over"]:
                                            game_state["turn"] = "defender" if game_state["turn"]=="attacker" else "attacker"
                                            status_msg = f"You moved to {mt}."
                                            if game_state["turn"] != human_side:
                                                do_computer_turn()
                                    else:
                                        pieces = ['A'] if human_side=="attacker" else ['D','K']
                                        if cell in pieces:
                                            selected=(rr,cc)
                                            all_mv=Hnefatafl.get_all_moves(game_state,human_side)
                                            valid_moves=[(f,t) for f,t in all_mv if f==(rr,cc)]
                                            status_msg=f"Selected ({rr},{cc}) — {len(valid_moves)} moves available"
                                        else:
                                            selected=None; valid_moves=[]
                                            status_msg="Click your own piece to select."
                                else:
                                    pieces = ['A'] if human_side=="attacker" else ['D','K']
                                    if cell in pieces:
                                        selected=(rr,cc)
                                        all_mv=Hnefatafl.get_all_moves(game_state,human_side)
                                        valid_moves=[(f,t) for f,t in all_mv if f==(rr,cc)]
                                        status_msg=f"Selected ({rr},{cc}) — {len(valid_moves)} moves available"

            # Check computer thread result
            if thinking and computer_result[0] is not None:
                mv = computer_result[0]; computer_result[0]=None; thinking=False
                if mv is None:
                    game_state["game_over"]=True; game_state["winner"]=human_side
                    status_msg="Computer has no moves! You win!"
                else:
                    frm,to = mv
                    Hnefatafl.move_piece(game_state,frm,to); Hnefatafl.detect_capture(game_state,to); Hnefatafl.win_condition(game_state)
                    last_move=(frm,to)
                    if not game_state["game_over"]:
                        game_state["turn"]="defender" if game_state["turn"]=="attacker" else "attacker"
                        status_msg=f"Computer moved {frm} to {to}. Your turn!"
                    else:
                        status_msg=f"Computer moved and the game is over!"

            # ── Render ──
            screen.fill(BG)
            draw_title(screen, fonts)
            draw_left_panel(screen, fonts, game_state, human_side, difficulty)
            draw_right_panel(screen, fonts, game_state, human_side, thinking, anim_t)
            draw_board(screen, fonts, game_state, selected, valid_moves, last_move, anim_t)
            draw_status(screen, fonts, status_msg)
            if game_state["game_over"]:
                draw_gameover(screen, fonts, game_state["winner"], human_side)

            pygame.display.flip()

        if restart:
            continue   # go back to top of outer while → show menu again

if __name__ == "__main__":
    main()
