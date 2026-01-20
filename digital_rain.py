import curses
import random
import time
import string

# Half-width Katakana (U+FF61 – U+FF9F)
HALF_WIDTH_KANA = (
    "｡｢｣､･"
    "ｦｧｨｩｪｫｬｭｮｯ"
    "ｰ"
    "ｱｲｳｴｵ"
    "ｶｷｸｹｺ"
    "ｻｼｽｾｿ"
    "ﾀﾁﾂﾃﾄ"
    "ﾅﾆﾇﾈﾉ"
    "ﾊﾋﾌﾍﾎ"
    "ﾏﾐﾑﾒﾓ"
    "ﾔﾕﾖ"
    "ﾗﾘﾙﾚﾛ"
    "ﾜﾝ"
)

ASCII = string.ascii_uppercase + "0123456789"

# Create reverse Roman letters
REVERSE_ASCII = ''.join(chr(ord('Z') - (ord(c)-ord('A'))) for c in string.ascii_uppercase)

# Final character pool for rain
CHARS = HALF_WIDTH_KANA + ASCII + REVERSE_ASCII

MESSAGES = [
    "WAKE UP, NEO",
    "FOLLOW THE WHITE RABBIT",
    "THE MATRIX HAS YOU",
    "SYSTEM ONLINE"
]

TRAIL = 6
HOLD_SECONDS = 4.0
PAUSE_BETWEEN = 2.0

# Fade stages: bright → normal → dim → gone
FADE_STEPS = [curses.A_BOLD, 0, curses.A_DIM]

def matrix(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    stdscr.nodelay(True)

    curses.init_pair(1, curses.COLOR_WHITE, -1)   # head
    curses.init_pair(2, curses.COLOR_GREEN, -1)   # trail
    curses.init_pair(3, curses.COLOR_GREEN, -1)   # message

    height, width = stdscr.getmaxyx()

    drops = [random.randint(0, height) for _ in range(width)]
    speeds = [random.uniform(0.02, 0.12) for _ in range(width)]
    timers = [0.0 for _ in range(width)]

    msg_index = 0
    locked = {}
    message_complete_time = None
    dissolve_mode = False
    pause_start = None

    def setup_message():
        nonlocal locked, message_complete_time, dissolve_mode
        locked = {}
        message_complete_time = None
        dissolve_mode = False

        msg = MESSAGES[msg_index]
        msg_y = height // 2
        msg_x = max(0, (width - len(msg)) // 2)
        cols = {msg_x + i: msg[i] for i in range(len(msg))}
        return msg, msg_y, cols

    message, msg_y, message_columns = setup_message()

    while True:
        stdscr.erase()
        height, width = stdscr.getmaxyx()

        for x in range(width):
            timers[x] += 0.05
            if timers[x] < speeds[x]:
                continue
            timers[x] = 0

            y = drops[x]

            # Head
            try:
                stdscr.addstr(y, x, random.choice(CHARS), curses.color_pair(1))
            except curses.error:
                pass

            # Trail
            for i in range(1, TRAIL):
                try:
                    stdscr.addstr((y - i) % height, x,
                                  random.choice(CHARS),
                                  curses.color_pair(2))
                except curses.error:
                    pass

            # Message logic
            if x in message_columns:
                if not dissolve_mode:
                    if x not in locked and y >= msg_y:
                        locked[x] = 0
                        if len(locked) == len(message_columns):
                            message_complete_time = time.time()
                    if x in locked:
                        stdscr.addstr(
                            msg_y, x,
                            message_columns[x],
                            curses.color_pair(3) | FADE_STEPS[locked[x]]
                        )
                else:
                    if x in locked:
                        stdscr.addstr(
                            msg_y, x,
                            message_columns[x],
                            curses.color_pair(3) | FADE_STEPS[locked[x]]
                        )

            drops[x] = (y + 1) % height

        now = time.time()

        # Hold → dissolve
        if message_complete_time and not dissolve_mode:
            if now - message_complete_time > HOLD_SECONDS:
                dissolve_mode = True

        if dissolve_mode and locked:
            x = random.choice(list(locked.keys()))
            locked[x] += 1
            if locked[x] >= len(FADE_STEPS):
                del locked[x]
            time.sleep(0.03)

        # Rotate message
        if dissolve_mode and not locked:
            pause_start = now
            dissolve_mode = False
            message_complete_time = None
            msg_index = (msg_index + 1) % len(MESSAGES)
            message, msg_y, message_columns = setup_message()

        if pause_start and now - pause_start >= PAUSE_BETWEEN:
            pause_start = None

        stdscr.refresh()
        time.sleep(0.05)

        key = stdscr.getch()
        if key in (ord('q'), ord('Q')):
            break

curses.wrapper(matrix)

