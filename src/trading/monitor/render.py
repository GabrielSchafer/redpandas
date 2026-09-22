import shutil
from datetime import datetime, timezone
from decimal import Decimal

from ..events.topics import ALL_TOPICS

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ACCENT = "\033[38;5;209m"
GREEN = "\033[38;5;71m"
RED = "\033[38;5;203m"
MUTED = "\033[38;5;245m"
HOME = "\033[H"
CLEAR = "\033[2J"
EOL = "\033[K"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"

LEFT_WIDTH = 46
GAP = 4
MAX_ACCOUNTS = 8


def paint(text: str, color: str) -> str:
    return f"{color}{text}{RESET}"


def cell(text: str, width: int, align: str = "<") -> str:
    text = str(text)
    if len(text) > width:
        text = text[: width - 1] + "…"
    return f"{text:{align}{width}}"


def amount(value) -> str:
    try:
        return f"{Decimal(str(value)):,.2f}"
    except Exception:
        return str(value)


def qty(value) -> str:
    try:
        return f"{Decimal(str(value)).normalize():,f}"
    except Exception:
        return str(value)


def short(topic: str) -> str:
    return topic.split(".", 1)[1] if "." in topic else topic


def header(state, brokers: str, width: int) -> list[str]:
    clock = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
    title = paint("REDPANDA TRADING MOCK", BOLD + ACCENT)
    meta = paint(f"{brokers} · {clock} · {state.total} events", MUTED)
    pad = max(1, width - 21 - len(f"{brokers} · {clock} · {state.total} events"))
    return [f"{title}{' ' * pad}{meta}", paint("─" * width, MUTED)]


def topics_pane(state) -> list[str]:
    lines = [paint(cell("TOPICS", 22) + cell("msgs", 7, ">") + "  last", BOLD)]
    for topic in ALL_TOPICS:
        count = state.counts.get(topic, 0)
        last = state.last_type.get(topic, "—")
        row = cell(short(topic), 22) + cell(count, 7, ">") + "  " + cell(last, 14)
        lines.append(row if count else paint(row, DIM))
    return lines


def tape_pane(state, width: int) -> list[str]:
    lines = [paint(cell("TAPE", 10) + cell("topic", 18) + "event", BOLD)]
    for stamp, topic, event_type, key in state.tape:
        color = GREEN if "filled" in event_type or "executed" in event_type else MUTED
        if "rejected" in event_type:
            color = RED
        row = cell(stamp, 10) + cell(short(topic), 18) + cell(f"{event_type}  {key}", max(10, width - 28))
        lines.append(paint(row, color))
    return lines


def book_pane(state) -> list[str]:
    symbol = state.symbol
    lines = [paint(cell(f"BOOK {symbol or '—'}", 22) + cell("qty", 8, ">") + cell("price", 12, ">"), BOLD)]
    if not symbol:
        return lines + [paint("  waiting for orders…", DIM)]
    depth = state.book(symbol)
    for level in reversed(depth["asks"]):
        lines.append(paint(cell("  ask", 22) + cell(qty(level["quantity"]), 8, ">") + cell(amount(level["price"]), 12, ">"), RED))
    if not depth["asks"]:
        lines.append(paint(cell("  ask", 22) + cell("—", 8, ">") + cell("—", 12, ">"), DIM))
    last = state.projection.last_price.get(symbol)
    lines.append(paint(cell("  last traded", 22) + cell("", 8) + cell(amount(last) if last else "—", 12, ">"), ACCENT))
    for level in depth["bids"]:
        lines.append(paint(cell("  bid", 22) + cell(qty(level["quantity"]), 8, ">") + cell(amount(level["price"]), 12, ">"), GREEN))
    if not depth["bids"]:
        lines.append(paint(cell("  bid", 22) + cell("—", 8, ">") + cell("—", 12, ">"), DIM))
    return lines


def accounts_pane(state, width: int) -> list[str]:
    symbol = state.symbol
    head = cell("ACCOUNTS", 16) + cell("cash", 14, ">") + cell("reserved", 13, ">") + cell(symbol or "position", 10, ">")
    lines = [paint(head, BOLD)]
    accounts = sorted(state.projection.accounts.items())
    for account_id, account in accounts[:MAX_ACCOUNTS]:
        balance = next(iter(account["balances"].values()), {"available": "0", "reserved": "0"})
        position = account["positions"].get(symbol, {}) if symbol else {}
        lines.append(
            cell(account_id, 16)
            + cell(amount(balance["available"]), 14, ">")
            + cell(amount(balance["reserved"]), 13, ">")
            + cell(qty(position.get("quantity", "0")), 10, ">")
        )
    hidden = len(accounts) - MAX_ACCOUNTS
    if hidden > 0:
        lines.append(paint(f"  … and {hidden} more accounts", DIM))
    if len(lines) == 1:
        lines.append(paint("  waiting for accounts…", DIM))
    return lines


def footer(state, width: int) -> list[str]:
    lines = [paint("─" * width, MUTED)]
    for account_id, reason in state.rejects:
        lines.append(paint(cell(f"rejected  {account_id}", 26) + reason, RED))
    lines.append(paint("ctrl-c to quit · read-only view, rebuilt from the log", DIM))
    return lines


def side_by_side(left: list[str], right: list[str], width: int) -> list[str]:
    rows = []
    for index in range(max(len(left), len(right))):
        left_cell = left[index] if index < len(left) else ""
        right_cell = right[index] if index < len(right) else ""
        visible = len(_strip(left_cell))
        rows.append(left_cell + " " * max(GAP, LEFT_WIDTH + GAP - visible) + right_cell)
    return rows


def _strip(text: str) -> str:
    out, skip = [], False
    for char in text:
        if char == "\033":
            skip = True
        elif skip and char == "m":
            skip = False
        elif not skip:
            out.append(char)
    return "".join(out)


def frame(state, brokers: str) -> str:
    width = min(shutil.get_terminal_size((110, 40)).columns, 130)
    right = max(30, width - LEFT_WIDTH - GAP)
    lines = header(state, brokers, width)
    lines += side_by_side(topics_pane(state), tape_pane(state, right), width)
    lines.append("")
    lines += side_by_side(book_pane(state), accounts_pane(state, right), width)
    lines += footer(state, width)
    return HOME + "\n".join(line + EOL for line in lines) + "\033[J"
