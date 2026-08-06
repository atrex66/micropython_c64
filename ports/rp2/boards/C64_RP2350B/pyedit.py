"""
Fix méretű terminálos Python szövegszerkesztő MicroPythonra.
Python szintaxis kiemelés, ANSI escape-ek, vágólap, billentyűkombinációk.
Méret: WIDTH x HEIGHT változókban, alapértelmezett 40×25.
"""

import sys
import os

try:
    import uselect
except ImportError:
    uselect = None

ESC = "\x1b"

# --- Fix terminál méret ---
WIDTH = 40
HEIGHT = 25

# Python kulcsszavak
KEYWORDS = {
    "False", "None", "True", "and", "as", "assert", "async", "await",
    "break", "class", "continue", "def", "del", "elif", "else", "except",
    "finally", "for", "from", "global", "if", "import", "in", "is",
    "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
    "try", "while", "with", "yield"
}

# ANSI színek
COLORS = {
    "keyword":  ESC + "[33m",
    "string":   ESC + "[32m",
    "comment":  ESC + "[90m",
    "number":   ESC + "[36m",
    "reset":    ESC + "[0m",
    "reverse":  ESC + "[7m",
    "unreverse": ESC + "[27m",
}


def _flush():
    """Biztonságos flush, ha támogatott."""
    try:
        sys.stdout.flush()
    except AttributeError:
        pass


def pad_right(s, width, fillchar=' '):
    """Kézi jobbra igazítás, MicroPython 'ljust' hiánya esetén."""
    s = s[:width]
    if len(s) < width:
        s += fillchar * (width - len(s))
    return s


def _read_byte(timeout=0):
    """Egy bájt beolvasása timeout-tal (ms), ha a uselect elérhető."""
    if uselect is None:
        return None
    poll = uselect.poll()
    poll.register(sys.stdin, uselect.POLLIN)
    res = poll.poll(timeout)
    if res:
        ch = sys.stdin.read(1)
        if isinstance(ch, bytes):
            return ch.decode("utf-8")
        return ch
    return None


class Editor:
    def __init__(self):
        self.buffer = [""]
        self.filename = None
        self.cursor_y = 0
        self.cursor_x = 0
        self.top_line = 0
        self.left_col = 0
        self.mark = None
        self.clipboard = []
        self.dirty = False
        self.message = ""
        self.screen_cols = WIDTH
        self.screen_rows = HEIGHT
        self.running = True
        self.input_mode = None
        self.quit_once = False

        self._set_raw()

    def _set_raw(self):
        """Nyers mód beállítása, ha lehetséges."""
        try:
            import tty
            import termios

            fd = sys.stdin.fileno()
            self.old_settings = termios.tcgetattr(fd)
            tty.setraw(fd)
        except Exception:
            self.old_settings = None

    def _restore_term(self):
        if self.old_settings:
            import termios

            termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, self.old_settings)

    # --- szintaxis kiemelés ---

    def _highlight_line(self, line):
        segments = []
        i = 0
        n = len(line)
        while i < n:
            if line[i] == "#":
                segments.append((line[i:], "comment"))
                break

            if line[i] in ('"', "'"):
                quote = line[i]
                start = i
                i += 1
                while i < n:
                    if line[i] == "\\":
                        i += 2
                    elif line[i] == quote:
                        i += 1
                        break
                    else:
                        i += 1
                segments.append((line[start:i], "string"))
                continue

            if line[i].isdigit() or (line[i] == "." and i + 1 < n and line[i + 1].isdigit()):
                start = i
                if line[i] == "0" and i + 1 < n and line[i + 1] in "xXbBoO":
                    i += 2
                    while i < n and (line[i].isdigit() or line[i] in "abcdefABCDEF_"):
                        i += 1
                else:
                    while i < n and (line[i].isdigit() or line[i] in ".eE+-_"):
                        i += 1
                segments.append((line[start:i], "number"))
                continue

            # Azonosítók: isalpha() vagy '_' a kezdés, utána isalpha(), isdigit() vagy '_'
            if line[i].isalpha() or line[i] == "_":
                start = i
                while i < n and (line[i].isalpha() or line[i].isdigit() or line[i] == "_"):
                    i += 1
                word = line[start:i]
                if word in KEYWORDS:
                    segments.append((word, "keyword"))
                else:
                    segments.append((word, None))
                continue

            segments.append((line[i], None))
            i += 1
        return segments

    # --- kijelölés kezelése ---

    def _get_ordered_selection(self):
        if self.mark is None:
            return None
        my, mx = self.mark
        cy, cx = self.cursor_y, self.cursor_x
        if my < cy or (my == cy and mx <= cx):
            return (my, mx), (cy, cx)
        else:
            return (cy, cx), (my, mx)

    # --- rajzolás ---

    def _draw_line(self, out, segments, line_idx, screen_row):
        out.append(ESC + "[{};1H".format(screen_row + 1))
        line_length = sum(len(t) for t, _ in segments)
        start_col = self.left_col
        end_col = start_col + self.screen_cols

        sel_range = None
        if self.mark is not None:
            sel = self._get_ordered_selection()
            (y1, x1), (y2, x2) = sel
            if y1 <= line_idx <= y2:
                sx1 = x1 if line_idx == y1 else 0
                sx2 = x2 if line_idx == y2 else line_length
                sel_range = (sx1, sx2)

        pos = 0
        for text, color in segments:
            seg_start = pos
            seg_end = pos + len(text)
            pos = seg_end
            if seg_end <= start_col or seg_start >= end_col:
                continue
            clip_start = max(start_col, seg_start)
            clip_end = min(end_col, seg_end)
            clip_text = text[clip_start - seg_start : clip_end - seg_start]
            self._output_text_with_selection(
                out, clip_text, color, line_idx, clip_start, clip_end, sel_range
            )
        out.append(ESC + "[K")

    def _output_text_with_selection(self, out, text, color, line_y, abs_start, abs_end, sel_range):
        if sel_range is None:
            if color:
                out.append(COLORS[color])
            out.append(text)
            if color:
                out.append(COLORS["reset"])
            return

        sx1, sx2 = sel_range
        idx = 0
        while idx < len(text):
            cur_pos = abs_start + idx
            in_sel = sx1 <= cur_pos < sx2
            j = idx
            while j < len(text):
                nxt_pos = abs_start + j
                if (sx1 <= nxt_pos < sx2) != in_sel:
                    break
                j += 1
            part = text[idx:j]
            if color:
                out.append(COLORS[color])
            if in_sel:
                out.append(COLORS["reverse"])
            out.append(part)
            if in_sel:
                out.append(COLORS["unreverse"])
            if color:
                out.append(COLORS["reset"])
            idx = j

    def _status_text(self):
        fname = self.filename if self.filename else "[Névtelen]"
        mod = " (módosítva)" if self.dirty else ""
        # Rövidített pozíció: S: sor O: oszlop
        pos = " S:{} O:{}".format(self.cursor_y + 1, self.cursor_x + 1)
        full = fname + mod + pos
        if len(full) <= self.screen_cols:
            return full

        # Számoljuk ki, mennyi hely marad a fájlnévnek
        available = self.screen_cols - len(mod) - len(pos)
        if available < 4:
            # Ha nagyon kevés a hely, csak a pozíciót mutatjuk
            return pos[:self.screen_cols]

        # Fájlnév rövidítése: eleje + "..." + vége
        if len(fname) > available:
            half = (available - 3) // 2
            if half < 1:
                half = 1
            fname_short = fname[:half] + "..." + fname[-half:]
        else:
            fname_short = fname

        return fname_short + mod + pos

    def _draw(self):
        out = []
        out.append(ESC + "[?25l")

        for screen_row in range(self.screen_rows - 1):
            line_idx = self.top_line + screen_row
            if line_idx < len(self.buffer):
                segments = self._highlight_line(self.buffer[line_idx])
                self._draw_line(out, segments, line_idx, screen_row)
            else:
                out.append(ESC + "[{};1H".format(screen_row + 1))
                out.append(ESC + "[K")

        status_row = self.screen_rows
        out.append(ESC + "[{};1H".format(status_row))
        out.append(COLORS["reverse"])
        status = pad_right(self._status_text(), self.screen_cols)
        out.append(status)
        out.append(COLORS["reset"])

        cy = self.cursor_y - self.top_line
        cx = self.cursor_x - self.left_col
        if cy < 0:
            cy = 0
        if cy >= self.screen_rows - 1:
            cy = self.screen_rows - 2
        if cx < 0:
            cx = 0
        if cx >= self.screen_cols:
            cx = self.screen_cols - 1
        out.append(ESC + "[{};{}H".format(cy + 1, cx + 1))
        out.append(ESC + "[?25h")

        sys.stdout.write("".join(out))
        _flush()

        if self.message:
            msg = pad_right(self.message, self.screen_cols)
            sys.stdout.write(
                ESC + "[{};1H".format(self.screen_rows)
                + COLORS["reverse"]
                + msg
                + COLORS["reset"]
            )
            sys.stdout.write(ESC + "[{};{}H".format(cy + 1, cx + 1))
            _flush()
            self.message = ""

    def _adjust_scroll(self):
        if self.cursor_x < self.left_col:
            self.left_col = self.cursor_x
        elif self.cursor_x >= self.left_col + self.screen_cols:
            self.left_col = self.cursor_x - self.screen_cols + 1
        if self.cursor_y < self.top_line:
            self.top_line = self.cursor_y
        elif self.cursor_y >= self.top_line + self.screen_rows - 1:
            self.top_line = self.cursor_y - (self.screen_rows - 2)

    # --- mozgás és szerkesztés ---

    def _move_up(self):
        if self.cursor_y > 0:
            self.cursor_y -= 1
            line_len = len(self.buffer[self.cursor_y])
            if self.cursor_x > line_len:
                self.cursor_x = line_len

    def _move_down(self):
        if self.cursor_y < len(self.buffer) - 1:
            self.cursor_y += 1
            line_len = len(self.buffer[self.cursor_y])
            if self.cursor_x > line_len:
                self.cursor_x = line_len

    def _move_left(self):
        if self.cursor_x > 0:
            self.cursor_x -= 1
        elif self.cursor_y > 0:
            self.cursor_y -= 1
            self.cursor_x = len(self.buffer[self.cursor_y])

    def _move_right(self):
        line = self.buffer[self.cursor_y]
        if self.cursor_x < len(line):
            self.cursor_x += 1
        elif self.cursor_y < len(self.buffer) - 1:
            self.cursor_y += 1
            self.cursor_x = 0

    def _move_home(self):
        self.cursor_x = 0

    def _move_end(self):
        self.cursor_x = len(self.buffer[self.cursor_y])

    def _move_page_up(self):
        self.cursor_y = max(0, self.cursor_y - (self.screen_rows - 2))

    def _move_page_down(self):
        self.cursor_y = min(len(self.buffer) - 1, self.cursor_y + (self.screen_rows - 2))

    def _word_left(self):
        line = self.buffer[self.cursor_y]
        while self.cursor_x > 0 and not (line[self.cursor_x - 1].isalpha() or line[self.cursor_x - 1].isdigit()) and line[self.cursor_x - 1] != '_':
            self.cursor_x -= 1
        while self.cursor_x > 0 and (line[self.cursor_x - 1].isalpha() or line[self.cursor_x - 1].isdigit() or line[self.cursor_x - 1] == '_'):
            self.cursor_x -= 1

    def _word_right(self):
        line = self.buffer[self.cursor_y]
        while self.cursor_x < len(line) and (line[self.cursor_x].isalpha() or line[self.cursor_x].isdigit() or line[self.cursor_x] == '_'):
            self.cursor_x += 1
        while self.cursor_x < len(line) and not (line[self.cursor_x].isalpha() or line[self.cursor_x].isdigit()) and line[self.cursor_x] != '_':
            self.cursor_x += 1

    def _delete_forward(self):
        line = self.buffer[self.cursor_y]
        if self.cursor_x < len(line):
            self.buffer[self.cursor_y] = line[: self.cursor_x] + line[self.cursor_x + 1:]
            self.dirty = True
        elif self.cursor_y < len(self.buffer) - 1:
            next_line = self.buffer.pop(self.cursor_y + 1)
            self.buffer[self.cursor_y] += next_line
            self.dirty = True

    def _delete_backward(self):
        if self.cursor_x > 0:
            line = self.buffer[self.cursor_y]
            self.buffer[self.cursor_y] = line[: self.cursor_x - 1] + line[self.cursor_x:]
            self.cursor_x -= 1
            self.dirty = True
        elif self.cursor_y > 0:
            current_line = self.buffer.pop(self.cursor_y)
            self.cursor_y -= 1
            self.cursor_x = len(self.buffer[self.cursor_y])
            self.buffer[self.cursor_y] += current_line
            self.dirty = True

    def _insert_newline(self):
        line = self.buffer[self.cursor_y]
        left = line[: self.cursor_x]
        right = line[self.cursor_x:]
        self.buffer[self.cursor_y] = left
        self.buffer.insert(self.cursor_y + 1, right)
        self.cursor_y += 1
        self.cursor_x = 0
        self.dirty = True

    def _insert_char(self, ch):
        line = self.buffer[self.cursor_y]
        self.buffer[self.cursor_y] = line[: self.cursor_x] + ch + line[self.cursor_x:]
        self.cursor_x += 1
        self.dirty = True

    def _insert_tab(self):
        self._insert_char(" " * 4)

    # --- vágólap / kijelölés ---

    def _toggle_mark(self):
        if self.mark is None:
            self.mark = (self.cursor_y, self.cursor_x)
        else:
            self.mark = None

    def _get_selection_text(self):
        if self.mark is None:
            return []
        (y1, x1), (y2, x2) = self._get_ordered_selection()
        if y1 == y2:
            return [self.buffer[y1][x1:x2]]
        lines = []
        lines.append(self.buffer[y1][x1:])
        for y in range(y1 + 1, y2):
            lines.append(self.buffer[y])
        lines.append(self.buffer[y2][:x2])
        return lines

    def _copy(self):
        txt = self._get_selection_text()
        if txt:
            self.clipboard = txt
            self.message = "Szöveg másolva"
        else:
            self.message = "Nincs kijelölés"

    def _cut(self):
        txt = self._get_selection_text()
        if not txt:
            self.message = "Nincs kijelölés"
            return
        self.clipboard = txt
        self._delete_selection()
        self.mark = None
        self.message = "Szöveg kivágva"

    def _delete_selection(self):
        if self.mark is None:
            return
        (y1, x1), (y2, x2) = self._get_ordered_selection()
        if y1 == y2:
            line = self.buffer[y1]
            self.buffer[y1] = line[:x1] + line[x2:]
        else:
            self.buffer[y1] = self.buffer[y1][:x1]
            self.buffer[y1] += self.buffer[y2][x2:]
            del self.buffer[y1 + 1 : y2 + 1]
        self.cursor_y, self.cursor_x = y1, x1
        self.dirty = True

    def _paste(self):
        if not self.clipboard:
            self.message = "Vágólap üres"
            return
        line = self.buffer[self.cursor_y]
        before = line[: self.cursor_x]
        after = line[self.cursor_x:]
        if len(self.clipboard) == 1:
            new_lines = [before + self.clipboard[0] + after]
            self.buffer[self.cursor_y : self.cursor_y + 1] = new_lines
            self.cursor_x = len(before) + len(self.clipboard[0])
        else:
            first = before + self.clipboard[0]
            middle = self.clipboard[1:-1]
            last = self.clipboard[-1] + after
            new_lines = [first] + middle + [last]
            self.buffer[self.cursor_y : self.cursor_y + 1] = new_lines
            self.cursor_y += len(self.clipboard) - 1
            self.cursor_x = len(last) - len(after)
        self.dirty = True
        self.mark = None
        self.message = "Szöveg beillesztve"

    # --- fájl műveletek ---

    def _save(self):
        if self.filename:
            try:
                with open(self.filename, "w") as f:
                    f.write("\n".join(self.buffer))
                self.dirty = False
                self.message = "Fájl mentve: " + self.filename
            except Exception as e:
                self.message = "Mentési hiba: " + str(e)
        else:
            self._start_input("Mentés másként: ", self._save_as_callback)

    def _save_as_callback(self, filename):
        if filename is None:
            self.message = "Mentés megszakítva"
            return
        self.filename = filename
        self._save()

    def _open(self):
        self._start_input("Fájl megnyitása: ", self._open_callback)

    def _open_callback(self, filename):
        if filename is None:
            self.message = "Megnyitás megszakítva"
            return
        try:
            with open(filename, "r") as f:
                content = f.read()
            self.buffer = content.split("\n")
            self.filename = filename
            self.cursor_y = 0
            self.cursor_x = 0
            self.top_line = 0
            self.left_col = 0
            self.mark = None
            self.dirty = False
            self.message = "Fájl betöltve: " + filename
        except Exception as e:
            self.message = "Megnyitási hiba: " + str(e)

    def _new_file(self):
        self.buffer = [""]
        self.filename = None
        self.cursor_y = 0
        self.cursor_x = 0
        self.top_line = 0
        self.left_col = 0
        self.mark = None
        self.dirty = False
        self.message = "Új fájl"

    def _quit(self):
        if self.dirty and not self.quit_once:
            self.message = "Nem mentett változások! Kilépéshez nyomd újra a Ctrl+Q-t"
            self.quit_once = True
        else:
            self.running = False

    # --- prompt kezelés ---

    def _start_input(self, prompt, callback):
        self.input_mode = {"prompt": prompt, "text": "", "callback": callback}
        self._draw_input_prompt()

    def _draw_input_prompt(self):
        if not self.input_mode:
            return
        disp = pad_right(self.input_mode["prompt"] + self.input_mode["text"], self.screen_cols)
        sys.stdout.write(
            ESC + "[{};1H".format(self.screen_rows)
            + COLORS["reverse"]
            + disp
            + COLORS["reset"]
        )
        _flush()

    def _handle_input_mode(self, key):
        if key[0] == "ENTER":
            text = self.input_mode["text"]
            cb = self.input_mode["callback"]
            self.input_mode = None
            cb(text)
        elif key[0] == "ESC":
            cb = self.input_mode["callback"]
            self.input_mode = None
            cb(None)
        elif key[0] == "BACKSPACE":
            if self.input_mode["text"]:
                self.input_mode["text"] = self.input_mode["text"][:-1]
                self._draw_input_prompt()
        elif key[0] == "CHAR":
            self.input_mode["text"] += key[1]
            self._draw_input_prompt()

    # --- billentyűzet olvasás ---

    def _get_key(self):
        c = sys.stdin.read(1)
        if isinstance(c, bytes):
            c = c.decode("utf-8")

        if c == "\x1b":
            c2 = _read_byte(50)
            if c2 is None:
                return ("ESC",)
            if c2 == "[":
                seq = ""
                while True:
                    ch = _read_byte(10)
                    if ch is None:
                        break
                    seq += ch
                    if ch.isalpha() or ch == "~":
                        break
                if seq == "A":
                    return ("UP",)
                if seq == "B":
                    return ("DOWN",)
                if seq == "C":
                    return ("RIGHT",)
                if seq == "D":
                    return ("LEFT",)
                if seq == "H":
                    return ("HOME",)
                if seq == "F":
                    return ("END",)
                if seq == "5~":
                    return ("PGUP",)
                if seq == "6~":
                    return ("PGDN",)
                if seq == "3~":
                    return ("DELETE",)
                if ";" in seq:
                    parts = seq.rstrip("ABCD~").split(";")
                    mod = parts[1] if len(parts) > 1 else ""
                    last_char = seq[-1]
                    if last_char == "A":
                        return ("SHIFT_UP",) if mod == "2" else ("CTRL_UP",) if mod == "5" else None
                    if last_char == "B":
                        return ("SHIFT_DOWN",) if mod == "2" else ("CTRL_DOWN",) if mod == "5" else None
                    if last_char == "C":
                        return ("SHIFT_RIGHT",) if mod == "2" else ("CTRL_RIGHT",) if mod == "5" else None
                    if last_char == "D":
                        return ("SHIFT_LEFT",) if mod == "2" else ("CTRL_LEFT",) if mod == "5" else None
            return None

        if c in ("\x7f", "\b"):
            return ("BACKSPACE",)
        if c in ("\n", "\r"):
            return ("ENTER",)
        if c == "\t":
            return ("TAB",)
        if c == "\x00":
            return ("CTRL_SPACE",)
        if 1 <= ord(c) <= 26:
            letter = chr(ord(c) + 96).upper()
            return ("CTRL_" + letter,)

        return ("CHAR", c)

    def _handle_key(self, key):
        if key is None:
            return
        if self.input_mode:
            self._handle_input_mode(key)
            return

        k = key[0]

        if k in ("UP", "DOWN", "LEFT", "RIGHT", "HOME", "END", "PGUP", "PGDN",
                 "CTRL_LEFT", "CTRL_RIGHT", "SHIFT_UP", "SHIFT_DOWN",
                 "SHIFT_LEFT", "SHIFT_RIGHT"):
            if k.startswith("SHIFT") and self.mark is None:
                self.mark = (self.cursor_y, self.cursor_x)
            if k == "UP":
                self._move_up()
            elif k == "DOWN":
                self._move_down()
            elif k == "LEFT":
                self._move_left()
            elif k == "RIGHT":
                self._move_right()
            elif k == "HOME":
                self._move_home()
            elif k == "END":
                self._move_end()
            elif k == "PGUP":
                self._move_page_up()
            elif k == "PGDN":
                self._move_page_down()
            elif k == "CTRL_LEFT":
                self._word_left()
            elif k == "CTRL_RIGHT":
                self._word_right()
            if not k.startswith("SHIFT") and k not in ("CTRL_LEFT", "CTRL_RIGHT"):
                if k != "CTRL_SPACE":
                    self.mark = None
        elif k == "CTRL_SPACE":
            self._toggle_mark()
        elif k == "DELETE":
            self._delete_forward()
            self.mark = None
        elif k == "BACKSPACE":
            self._delete_backward()
            self.mark = None
        elif k == "ENTER":
            self._insert_newline()
            self.mark = None
        elif k == "TAB":
            self._insert_tab()
            self.mark = None
        elif k == "ESC":
            self.mark = None
            self.quit_once = False
            self.message = ""
        elif k.startswith("CTRL_"):
            ctrl_key = k[5:]
            if ctrl_key == "C":
                self._copy()
            elif ctrl_key == "X":
                self._cut()
            elif ctrl_key == "V":
                self._paste()
            elif ctrl_key == "S":
                self._save()
                self.quit_once = False
            elif ctrl_key == "O":
                self._open()
            elif ctrl_key == "N":
                self._new_file()
            elif ctrl_key == "Q":
                self._quit()
            elif ctrl_key == "L":
                self._refresh_screen()
        elif k == "CHAR":
            self._insert_char(key[1])
            self.mark = None
            self.quit_once = False

    def _refresh_screen(self):
        sys.stdout.write(ESC + "[2J" + ESC + "[H")
        _flush()
        self._adjust_scroll()
        self._draw()

    # --- fő ciklus ---

    def main(self):
        sys.stdout.write(ESC + "[2J" + ESC + "[H")
        _flush()
        self._draw()
        while self.running:
            key = self._get_key()
            self._handle_key(key)
            self._adjust_scroll()
            self._draw()
        self._restore_term()
        sys.stdout.write(ESC + "[2J" + ESC + "[H")
        _flush()


if __name__ == "__main__":
    Editor().main()