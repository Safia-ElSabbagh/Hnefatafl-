import copy

# ═══════════════════════════════════════════════════════════════════════════════
#  GAME LOGIC
# ═══════════════════════════════════════════════════════════════════════════════

boardsize = 11

# Difficulty controls depth of AI search
DIFFICULTY_DEPTH = {"easy": 1, "medium": 2, "hard": 3}

center = boardsize // 2

# special positions
throne_position = (center, center)
corner_positions = [
    (0, 0), (0, boardsize - 1),
    (boardsize - 1, 0), (boardsize - 1, boardsize - 1)
]


# Create initial board with attackers (A), defenders (D), king (K)
def make_initial_board():
    board = [['-'] * boardsize for _ in range(boardsize)]

    # king in center
    board[center][center] = "K"

    # defenders
    for pos in [
        (center, center - 1), (center, center + 1), (center - 1, center), (center + 1, center),
        (center - 2, center), (center + 2, center), (center, center - 2), (center, center + 2),
        (center - 1, center - 1), (center - 1, center + 1), (center + 1, center - 1), (center + 1, center + 1)
    ]:
        board[pos[0]][pos[1]] = "D"

    # attackers
    for pos in [
        (center, 0), (center, 1), (center - 1, 0), (center - 2, 0), (center + 1, 0), (center + 2, 0),
        (center, boardsize - 1), (center, boardsize - 2), (center - 1, boardsize - 1), (center - 2, boardsize - 1),
        (center + 1, boardsize - 1), (center + 2, boardsize - 1),
        (0, center), (1, center), (0, center - 1), (0, center - 2), (0, center + 1), (0, center + 2),
        (boardsize - 1, center), (boardsize - 2, center), (boardsize - 1, center - 1), (boardsize - 1, center - 2),
        (boardsize - 1, center + 1), (boardsize - 1, center + 2)
    ]:
        board[pos[0]][pos[1]] = "A"

    # Corners
    for pos in corner_positions:
        board[pos[0]][pos[1]] = "X"
    return board


# Initialize full game state
def make_initial_state():
    return {
        "board": make_initial_board(),
        "turn": "attacker",
        "captured_attackers": 0,
        "captured_defenders": 0,
        "game_over": False,
        "winner": None
    }


# Move piece from one position to another
def move_piece(game_state, frm, to):
    b = game_state["board"]
    b[to[0]][to[1]] = b[frm[0]][frm[1]]
    b[frm[0]][frm[1]] = '-'


# Remove piece (used in capture logic)
def remove_piece(game_state, pos):
    b = game_state["board"];
    r, c = pos
    p = b[r][c]

    if p == 'A':
        game_state["captured_attackers"] += 1
    elif p == 'D':
        game_state["captured_defenders"] += 1

    b[r][c] = '-'


# Detect capture after a move
def detect_capture(game_state, pos):
    b = game_state["board"];
    r, c = pos;
    piece = b[r][c]

    # determine enemy type
    if piece == 'A':
        enemy = 'D'
    elif piece == 'D':
        enemy = 'A'
    else:
        return

    cap = []
    # Check 4 directions for sandwich capture
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        mr, mc = r + dr, c + dc;
        er, ec = r + 2 * dr, c + 2 * dc

        if 0 <= mr < boardsize and 0 <= mc < boardsize and 0 <= er < boardsize and 0 <= ec < boardsize:
            # Special rule: defender can't be captured via king
            if b[mr][mc] == enemy:
                if piece == 'D' and b[er][ec] == 'K': continue

                # Valid sandwich condition
                if b[er][ec] == piece or (er, ec) == throne_position or (er, ec) in corner_positions:
                    cap.append((mr, mc))

    # Remove captured enemies
    for p2 in cap: remove_piece(game_state, p2)

    # Check if current piece gets captured
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        r1, c1 = r + dr, c + dc;
        r2, c2 = r - dr, c - dc

        if 0 <= r1 < boardsize and 0 <= c1 < boardsize and 0 <= r2 < boardsize and 0 <= c2 < boardsize:
            s1 = b[r1][c1];
            s2 = b[r2][c2]
            e1 = (s1 == enemy or (r1, c1) == throne_position or (r1, c1) in corner_positions)
            e2 = (s2 == enemy or (r2, c2) == throne_position or (r2, c2) in corner_positions)

            if e1 and e2:
                remove_piece(game_state, (r, c));
                return


# Check win conditions
def win_condition(game_state):
    b = game_state["board"]
    k = None

    # find king
    for r in range(boardsize):
        for c in range(boardsize):
            if b[r][c] == 'K':
                k = (r, c)
                break
        if k: break

    # King captured: attackers win
    if not k:
        game_state["game_over"] = True
        game_state["winner"] = "attacker"
        return

    kr, kc = k

    # King reaches corner: defenders win
    if k in corner_positions:
        game_state["game_over"] = True
        game_state["winner"] = "defender"
        return

    # King surrounded on 4 sides: attackers win
    def A(r, c):
        return 0 <= r < boardsize and 0 <= c < boardsize and b[r][c] == 'A'

    if A(kr - 1, kc) and A(kr + 1, kc) and A(kr, kc - 1) and A(kr, kc + 1):
        game_state["game_over"] = True
        game_state["winner"] = "attacker"
        return

    # Edge and corner capture rules
    if (kr == 0 and A(kr + 1, kc) and A(kr, kc + 1) and A(kr, kc - 1)) or \
            (kr == boardsize - 1 and A(kr - 1, kc) and A(kr, kc + 1) and A(kr, kc - 1)) or \
            (kc == 0 and A(kr - 1, kc) and A(kr + 1, kc) and A(kr, kc + 1)) or \
            (kc == boardsize - 1 and A(kr - 1, kc) and A(kr + 1, kc) and A(kr, kc - 1)):
        game_state["game_over"] = True;
        game_state["winner"] = "attacker";
        return

    if (kr == 0 and kc == 0 and A(kr + 1, kc) and A(kr, kc + 1)) or \
            (kr == 0 and kc == boardsize - 1 and A(kr + 1, kc) and A(kr, kc - 1)) or \
            (kr == boardsize - 1 and kc == 0 and A(kr - 1, kc) and A(kr, kc + 1)) or \
            (kr == boardsize - 1 and kc == boardsize - 1 and A(kr - 1, kc) and A(kr, kc - 1)):
        game_state["game_over"] = True;
        game_state["winner"] = "attacker";
        return


# MOVE GENERATION (VALID MOVES)
def get_all_moves(game_state, player):
    b = game_state["board"]
    pieces = ['A'] if player == "attacker" else ['D', 'K'];
    moves = []

    for r in range(boardsize):
        for c in range(boardsize):
            # Skip if not player's piece
            if b[r][c] not in pieces:
                continue

            # Explore 4 directions (rook-like movement)
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc

                # Move until blocked
                while 0 <= nr < boardsize and 0 <= nc < boardsize:
                    # Stop if another piece blocks
                    if b[nr][nc] != '-':
                        # King can move into corners
                        if b[r][c] == 'K' and (nr, nc) in corner_positions:
                            moves.append(((r, c), (nr, nc)))
                        break
                    # Non-king cannot enter throne or corners
                    if b[r][c] != 'K' and ((nr, nc) == throne_position or (nr, nc) in corner_positions):
                        nr += dr;
                        nc += dc;
                        continue
                    # Valid move
                    moves.append(((r, c), (nr, nc)))
                    nr += dr
                    nc += dc
    return moves


# creates a deep copy of the game_state, so the computer apply moves on it not the original one
def apply_move_copy(game_state, frm, to):
    ns = copy.deepcopy(game_state)
    move_piece(ns, frm, to);
    detect_capture(ns, to);
    win_condition(ns)
    ns["turn"] = "defender" if ns["turn"] == "attacker" else "attacker"
    return ns


# Utility function for AI evaluation
def heuristic(game_state):
    b = game_state["board"]
    # If game ended → return extreme values
    if game_state["game_over"]:
        return 10000 if game_state["winner"] == "attacker" else -10000

    # Find king position
    k = None
    for r in range(boardsize):
        for c in range(boardsize):
            if b[r][c] == 'K':
                k = (r, c)
                break
        if k: break

    if not k:
        return 10000  # King dead attackers winning

    kr, kc = k
    score = 0

    #Piece count advantage
    # more attackers alive = good for attacker (+)
    # more defenders alive = good for defender (-)
    ac = sum(1 for r in range(boardsize) for c in range(boardsize) if b[r][c] == 'A')
    dc = sum(1 for r in range(boardsize) for c in range(boardsize) if b[r][c] == 'D')
    score += (ac - dc) * 10

    #King distance to nearest corner
    # farther from corner = better for attacker (+)
    # closer to corner = better for defender (-)
    score += min(abs(kr - cr) + abs(kc - cc) for cr, cc in corner_positions) * 5

    #How many sides of the king are threatened
    # more surrounded = better for attacker (+)
    sur = sum(1 for dr, dc2 in [(-1, 0), (1, 0), (0, -1), (0, 1)]
              if not (0 <= kr + dr < boardsize and 0 <= kc + dc2 < boardsize) or b[kr + dr][kc + dc2] == 'A')
    score += sur * 15

    #King mobility
    # fewer moves = better for attacker (+)
    # more moves = better for defender (-)
    km = 0
    for dr, dc2 in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = kr + dr, kc + dc2
        while 0 <= nr < boardsize and 0 <= nc < boardsize:
            if b[nr][nc] != '-': break
            km += 1;
            nr += dr;
            nc += dc2
    score -= km * 3

    # Defender mobility
    # more defender moves = better for defender (-)
    # fewer defender moves = better for attacker (+)
    score -= len(get_all_moves(game_state, "defender")) * 2

    # Attacker proximity to king
    # attackers close to king = better for attacker (+)
    score += sum(1 for r in range(boardsize) for c in range(boardsize)
                 if b[r][c] == 'A' and abs(r - kr) + abs(c - kc) <= 3) * 4

    #King escape path control
    # check if king has a clear path to any corner
    # clear path = bad for attacker (-), good for defender
    for cr, cc in corner_positions:
        clear = True
        # check horizontal then vertical path to corner
        if kr == cr:
            st = 1 if cc > kc else -1
            for c2 in range(kc + st, cc, st):
                if b[kr][c2] != '-': clear = False; break
        elif kc == cc:
            st = 1 if cr > kr else -1
            for r2 in range(kr + st, cr, st):
                if b[r2][kc] != '-': clear = False; break
        else:
            clear = False  # not aligned with corner
        if clear:
            score -= 30  # open escape path is very dangerous for attacker

    # Attacker control of escape routes
    # attackers blocking corner paths = good for attacker (+)
    for cr, cc in corner_positions:
        # check if any attacker is between king and corner horizontally
        if kr == cr:
            step = 1 if cc > kc else -1
            for c in range(kc + step, cc, step):
                if b[kr][c] == 'A':
                    score += 8
                    break
        # check if any attacker is between king and corner vertically
        elif kc == cc:
            step = 1 if cr > kr else -1
            for r in range(kr + step, cr, step):
                if b[r][kc] == 'A':
                    score += 8
                    break

    return score


def alpha_beta(game_state, depth, alpha, beta, maximizing):
    if game_state["game_over"]:
        return (10000 + depth, None) if game_state["winner"] == "attacker" else (
        -10000 - depth, None)  # faster win = higher score

    # base condition to exit
    if depth == 0:
        return heuristic(game_state), None

    player = "attacker" if maximizing else "defender"
    moves = get_all_moves(game_state, player)  # get all moves for the player

    if not moves:
        # if a player has can't move no more then it loses
        return (-10000 - depth, None) if maximizing else (10000 + depth, None)

    best = None

    if maximizing:  ##attacker
        best_s = float('-inf')  ##intialize with -infinity awl score kda kda hykon akbar mnha
        for f, t in moves:  ##loop on all possible moves
            ##recursive call on depth-1 return score from child , - means m4 mohtam bl child moves
            ### false 34an a switch ben max w min (attacker, defender)
            s, _ = alpha_beta(apply_move_copy(game_state, f, t), depth - 1, alpha, beta, False)
            # lw score from child akbar mn current best
            # update best score and best move
            if s > best_s:
                best_s = s
                best = (f, t)  ##new best move
            alpha = max(alpha, best_s)  ###update alpha bl new alpha (new best score)
            if beta <= alpha:  ##alpha akbar mn el beta cut
                break
        return best_s, best
    else:  ##defender
        best_s = float('inf')  ###we minimize so initialize with inf ay score hyb2a as8ar mnha
        for f, t in moves:
            ##recursive call on depth-1 return score from child
            ### true 34an a switch ben max w min (attacker, defender)
            s, _ = alpha_beta(apply_move_copy(game_state, f, t), depth - 1, alpha, beta, True)
            # lw score from child as8ar mn current best
            # update best score and best move
            if s < best_s:
                best_s = s
                best = (f, t)
            # update beta bl as8ar
            beta = min(beta, best_s)
            if beta <= alpha:
                break
        return best_s, best


def get_computer_move(game_state, diff):
    ##get el difficulty level a b3mlo path ll alpha beta intiale values ll alpha -inf w beta inf
    d = DIFFICULTY_DEPTH.get(diff, 2)
    _, m = alpha_beta(game_state, d, float('-inf'), float('inf'), game_state["turn"] == "attacker")
    return m