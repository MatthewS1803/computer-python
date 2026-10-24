#!/usr/bin/env python3
"""
Search formulation
------------------
State        : (shares held of each stock, cash in cents)
Start state  : the current portfolio
Goal test    : every stock's holding lies inside its target band
               (band = exact target, or +/- tolerance %)
Actions      : buy / sell one lot (1, 10, 100 ... shares) of one stock
Legality     : never < 0 shares, never < $0 cash after ANY trade,
               sell-only (delisted) stocks can't be bought
Action cost  : the flat fee (identical for every action)

Algorithms
----------
* A*  - heuristic = sum over stocks of the minimum number of lot-trades needed
        to bring that stock into its goal band, IGNORING cash. Ignoring the cash
        constraint only makes the problem easier, so it never over-estimates
        (admissible); and it is the true shortest-path distance in a relaxed
        graph, so it is also consistent. A* is therefore optimal.
* BFS - uninformed baseline. Also optimal (all costs equal) but expands far
        more nodes. Useful for comparing against A*.

"""

from __future__ import annotations

import heapq
import itertools
import math
import queue
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Callable, Dict, List, Optional, Sequence, Tuple

try:  # the solver can be imported / tested without a display
    import tkinter as tk
    from tkinter import font as tkfont
    from tkinter import messagebox, ttk
except ImportError:  # pragma: no cover
    tk = ttk = messagebox = tkfont = None


def money(cents: int) -> str:
    """Format integer cents as a dollar string, e.g. 123456 -> '$1,234.56'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}${cents // 100:,}.{cents % 100:02d}"


def to_cents(text) -> int:
    """Parse a user-typed dollar amount ('12.34', '$1,000') into integer cents.
 
    Uses Decimal (not float) so that e.g. '0.10' is exactly 10 cents.
    Raises ValueError with a friendly message if the text isn't a number.
    """ 
    try:
        d = Decimal(str(text).replace("$", "").replace(",", "").strip())
    except InvalidOperation:
        raise ValueError(f"'{text}' is not a valid dollar amount")
    return int((d * 100).to_integral_value())


@dataclass
class Problem:
    symbols: List[str]
    prices: List[int]                 # cents per share (fixed for the whole problem)
    sell_only: List[bool]
    start_holdings: Tuple[int, ...]
    start_cash: int                   # cents
    bands: List[Tuple[int, int]]      # (lo, hi) acceptable final holdings per stock
    lots: Tuple[int, ...] = (1, 10, 100)
    fee: int = 500                    # cents per trade

    def is_goal(self, holdings: Sequence[int]) -> bool:
        return all(lo <= h <= hi for h, (lo, hi) in zip(holdings, self.bands))


def make_band(target: int, tol_pct: Decimal) -> Tuple[int, int]:
    """Goal band for a target quantity. tol_pct = 0 -> exact."""
    if tol_pct == 0:
        return target, target
    lo = math.ceil(Decimal(target) * (Decimal(100) - tol_pct) / 100)
    hi = math.floor(Decimal(target) * (Decimal(100) + tol_pct) / 100)
    return int(lo), int(hi)


@dataclass
class Move:
    stock: int
    kind: str      # "BUY" or "SELL"
    lot: int


@dataclass
class Result:
    status: str                       # solved | no_solution | limit | cancelled
    moves: List[Move] = field(default_factory=list)
    expanded: int = 0
    generated: int = 0
    seconds: float = 0.0
    message: str = ""


class Solver:
    """Runs A* or BFS over the trade state space for one Problem."""
    def __init__(self, problem: Problem):
        self.p = problem
        n = len(problem.symbols)
        maxlot = max(problem.lots)
        # Upper limit on how many shares of each stock a state may hold.
        # Without a cap the space would be infinite (you could keep buying).
        self.caps = [
            max(problem.start_holdings[i], problem.bands[i][1], maxlot) * 2 + 3 * maxlot
            for i in range(n)
        ]
        self.dist = [self._stock_distances(i) for i in range(n)]

    # ---- heuristic ---------------------------------------------------------
    def _stock_distances(self, i: int) -> List[Optional[int]]:
        """dist[h] = min # of lot trades to take stock i from h shares into its band,
        ignoring cash. Computed by reverse BFS from the band."""
        p = self.p
        cap = self.caps[i]
        lo, hi = p.bands[i]
        dist: List[Optional[int]] = [None] * (cap + 1)
        dq = deque()
        for h in range(max(lo, 0), min(hi, cap) + 1):
            dist[h] = 0
            dq.append(h)
        can_buy = not p.sell_only[i]
        while dq:
            v = dq.popleft()
            for L in p.lots:
                u = v - L            # u --buy L--> v
                if can_buy and u >= 0 and dist[u] is None:
                    dist[u] = dist[v] + 1
                    dq.append(u)
                u = v + L            # u --sell L--> v
                if u <= cap and dist[u] is None:
                    dist[u] = dist[v] + 1
                    dq.append(u)
        return dist

    def heuristic(self, holdings: Sequence[int]) -> Optional[int]:
        total = 0
        for i, h in enumerate(holdings):
            d = self.dist[i][h]
            if d is None:
                return None          # this stock can never reach its band
            total += d
        return total

    # ---- successors --------------------------------------------------------
    def successors(self, holdings: Tuple[int, ...], cash: int):
        p = self.p
        for i in range(len(holdings)):
            price = p.prices[i]
            h = holdings[i]
            for L in p.lots:
                # BUY
                if not p.sell_only[i] and h + L <= self.caps[i]:
                    new_cash = cash - L * price - p.fee
                    if new_cash >= 0:
                        nh = holdings[:i] + (h + L,) + holdings[i + 1:]
                        yield Move(i, "BUY", L), (nh, new_cash)
                # SELL
                if h >= L:
                    new_cash = cash + L * price - p.fee
                    if new_cash >= 0:
                        nh = holdings[:i] + (h - L,) + holdings[i + 1:]
                        yield Move(i, "SELL", L), (nh, new_cash)

    # ---- search ------------------------------------------------------------
    def solve(
        self,
        algo: str = "astar",
        node_limit: int = 3_000_000,
        cancel: Optional[threading.Event] = None,
        progress: Optional[Callable[[int], None]] = None,
    ) -> Result:
        t0 = time.time()
        p = self.p
        start = (p.start_holdings, p.start_cash)

        def done(status, moves=(), exp=0, gen=0, msg=""):
            return Result(status, list(moves), exp, gen, time.time() - t0, msg)

        if p.is_goal(p.start_holdings):
            return done("solved", msg="You already hold the goal portfolio.")

        h0 = self.heuristic(p.start_holdings)
        if h0 is None:
            return done("no_solution",
                        msg="A sell-only stock would have to be bought to reach the goal.")

        # Quick necessary condition: wealth can only shrink (by the fees), and the
        # final portfolio must be worth at least the lower edge of every band.
        wealth = p.start_cash + sum(h * pr for h, pr in zip(p.start_holdings, p.prices))
        need = sum(lo * pr for (lo, _), pr in zip(p.bands, p.prices))
        if wealth - h0 * p.fee < need:
            return done("no_solution",
                        msg=("Not enough money: even with the fewest possible trades the "
                             f"goal costs at least {money(need + h0 * p.fee)} but your "
                             f"portfolio + cash is worth {money(wealth)}."))

        return self._astar(start, h0, node_limit, cancel, progress, t0) \
            if algo == "astar" else \
            self._bfs(start, node_limit, cancel, progress, t0)

    def _rebuild(self, parents, state) -> List[Move]:
        moves = []
        while parents[state] is not None:
            state, mv = parents[state]
            moves.append(mv)
        moves.reverse()
        return moves

    def _astar(self, start, h0, node_limit, cancel, progress, t0) -> Result:
        counter = itertools.count()
        openq = [(h0, 0, next(counter), start, 0)]     # (f, -g, tie, state, g)
        best_g = {start: 0}
        parents = {start: None}
        expanded = generated = 0
        while openq:
            f, _, _, state, g = heapq.heappop(openq)
            if g > best_g.get(state, 1 << 60):
                continue                                # stale queue entry
            holdings, cash = state
            if self.p.is_goal(holdings):
                return Result("solved", self._rebuild(parents, state), expanded,
                              generated, time.time() - t0)
            expanded += 1
            if expanded % 2000 == 0:
                if cancel is not None and cancel.is_set():
                    return Result("cancelled", [], expanded, generated, time.time() - t0)
                if progress:
                    progress(expanded)
            if expanded >= node_limit:
                return Result("limit", [], expanded, generated, time.time() - t0,
                              f"Stopped after {node_limit:,} expanded nodes.")
            for mv, ns in self.successors(holdings, cash):
                ng = g + 1
                if ng < best_g.get(ns, 1 << 60):
                    h = self.heuristic(ns[0])
                    if h is None:
                        continue
                    best_g[ns] = ng
                    parents[ns] = (state, mv)
                    generated += 1
                    heapq.heappush(openq, (ng + h, -ng, next(counter), ns, ng))
        return Result("no_solution", [], expanded, generated, time.time() - t0,
                      "Search space exhausted - no legal sequence of trades reaches the goal.")

    def _bfs(self, start, node_limit, cancel, progress, t0) -> Result:
        parents = {start: None}
        frontier = deque([start])
        expanded = generated = 0
        while frontier:
            state = frontier.popleft()
            expanded += 1
            if expanded % 2000 == 0:
                if cancel is not None and cancel.is_set():
                    return Result("cancelled", [], expanded, generated, time.time() - t0)
                if progress:
                    progress(expanded)
            if expanded >= node_limit:
                return Result("limit", [], expanded, generated, time.time() - t0,
                              f"Stopped after {node_limit:,} expanded nodes "
                              "(BFS explores far more states than A*; try A*).")
            holdings, cash = state
            for mv, ns in self.successors(holdings, cash):
                if ns in parents:
                    continue
                parents[ns] = (state, mv)
                generated += 1
                # unit costs => the first goal found is optimal
                if self.p.is_goal(ns[0]):
                    return Result("solved", self._rebuild(parents, ns), expanded,
                                  generated, time.time() - t0)
                frontier.append(ns)
        return Result("no_solution", [], expanded, generated, time.time() - t0,
                      "Search space exhausted - no legal sequence of trades reaches the goal.")


PALETTES = {
    "light": dict(
        bg="#F1F4F9", card="#FFFFFF", chip="#F3F4F8", text="#1F2937", muted="#6B7280",
        border="#DDE1EA", input="#FFFFFF", accent="#4F46E5", accent_hover="#4338CA",
        accent_fg="#FFFFFF", header="#4F46E5", header_fg="#FFFFFF", btn="#EEF0F6",
        btn_hover="#E1E5EF", sel="#E0E7FF",
        buy_bg="#E9F8EF", buy_fg="#15803D", sell_bg="#FDEDED", sell_fg="#B91C1C",
        warn="#B45309", disabled="#A5A9C9"),
    "dark": dict(
        bg="#0B1120", card="#151E32", chip="#0F1729", text="#E5E7EB", muted="#94A3B8",
        border="#2A3550", input="#0F1729", accent="#6366F1", accent_hover="#818CF8",
        accent_fg="#FFFFFF", header="#1E1B4B", header_fg="#FFFFFF", btn="#222E48",
        btn_hover="#2C3A5C", sel="#2A3A6A",
        buy_bg="#10291D", buy_fg="#4ADE80", sell_bg="#33161A", sell_fg="#F87171",
        warn="#FBBF24", disabled="#475069"),
}


def _fixed_map(style, option):
    return [e for e in style.map("Treeview", query_opt=option)
            if e[:2] != ("!disabled", "!selected")]


class Card(tk.Frame if tk else object):
    """A white 'card' with a thin border, used to group controls."""

    def __init__(self, master, app, title=None, subtitle=None):
        super().__init__(master, highlightthickness=1, bd=0)
        app.themed.append(lambda t: self.configure(
            bg=t["card"], highlightbackground=t["border"], highlightcolor=t["border"]))
        self.body = ttk.Frame(self, style="Card.TFrame")
        if title:
            head = ttk.Frame(self, style="Card.TFrame")
            head.pack(fill="x", padx=16, pady=(12, 0))
            ttk.Label(head, text=title, style="CardTitle.TLabel").pack(side="left")
            if subtitle:
                ttk.Label(head, text=subtitle, style="CardSub.TLabel").pack(side="left", padx=(10, 0), pady=(3, 0))
        self.body.pack(fill="both", expand=True, padx=16, pady=(8, 14))


class RowTable(ttk.Frame):
    """Editable table: one row per stock, with a scrollable body."""

    def __init__(self, master, app, columns, height=132, on_change=None):
        super().__init__(master, style="Card.TFrame")
        self.columns = columns            # (header, kind, width)
        self.on_change = on_change or (lambda: None)
        self.rows: List[List] = []
        self._widgets: List[List] = []

        self.canvas = tk.Canvas(self, height=height, highlightthickness=0, bd=0)
        app.themed.append(lambda t: self.canvas.configure(bg=t["card"]))
        sb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas, style="Card.TFrame")
        self._win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self._win, width=e.width))
        self.canvas.configure(yscrollcommand=sb.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns", padx=(6, 0))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        for c, (hdr, kind, _) in enumerate(columns):
            ttk.Label(self.inner, text=hdr.upper(), style="Field.TLabel").grid(
                row=0, column=c, padx=(0, 8), pady=(0, 4), sticky="w")
            if kind != "check":
                self.inner.columnconfigure(c, weight=1)

        for w in (self.canvas, self.inner):
            w.bind("<Enter>", self._bind_wheel)
            w.bind("<Leave>", self._unbind_wheel)

    # mouse wheel scrolling only while hovering the table
    def _bind_wheel(self, _e):
        self.canvas.bind_all("<MouseWheel>", self._wheel)
        self.canvas.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))

    def _unbind_wheel(self, _e):
        for ev in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.canvas.unbind_all(ev)

    def _wheel(self, e):
        self.canvas.yview_scroll(-1 if e.delta > 0 else 1, "units")

    def add_row(self, values=None, notify=True):
        values = values or [""] * len(self.columns)
        r = len(self.rows) + 1
        vars_, widgets = [], []
        for c, (hdr, kind, width) in enumerate(self.columns):
            if kind == "check":
                v = tk.BooleanVar(value=bool(values[c]))
                w = ttk.Checkbutton(self.inner, variable=v, style="Card.TCheckbutton")
                w.grid(row=r, column=c, padx=(0, 8), pady=3, sticky="w")
            else:
                v = tk.StringVar(value=str(values[c]))
                w = ttk.Entry(self.inner, textvariable=v, width=width)
                w.grid(row=r, column=c, padx=(0, 8), pady=3, sticky="ew")
                if c == 0:
                    w.bind("<FocusOut>", lambda e, var=v: var.set(var.get().strip().upper()))
            v.trace_add("write", lambda *a: self.on_change())
            vars_.append(v)
            widgets.append(w)
        d = ttk.Label(self.inner, text="✕", style="Del.TLabel", cursor="hand2", width=3, anchor="center")
        d.grid(row=r, column=len(self.columns), pady=3)
        d.bind("<Enter>", lambda e, w=d: w.configure(style="DelHover.TLabel"))
        d.bind("<Leave>", lambda e, w=d: w.configure(style="Del.TLabel"))
        d.bind("<Button-1>", lambda e, ws=widgets: self._delete(ws))
        widgets.append(d)
        self.rows.append(vars_)
        self._widgets.append(widgets)
        if notify:
            self.on_change()

    def _delete(self, widgets):
        idx = self._widgets.index(widgets)
        for w in widgets:
            w.destroy()
        del self._widgets[idx]
        del self.rows[idx]
        for r, ws in enumerate(self._widgets, start=1):
            for w in ws:
                w.grid_configure(row=r)
        self.on_change()

    def clear(self):
        for ws in self._widgets:
            for w in ws:
                w.destroy()
        self._widgets.clear()
        self.rows.clear()
        self.on_change()

    def values(self):
        return [[v.get() for v in row] for row in self.rows]


class TradePlannerApp:
    def __init__(self, root):
        self.root = root
        root.title("Trade Planner")
        root.geometry("1200x900")
        root.minsize(1000, 760)
        self.q: queue.Queue = queue.Queue()
        self.cancel_event = threading.Event()
        self.problem: Optional[Problem] = None
        self.themed: List[Callable] = []
        self.mode = "light"

        fams = set(tkfont.families())
        self.family = next((f for f in ("Segoe UI", "SF Pro Text", "Helvetica Neue", "Inter",
                                        "Ubuntu", "Noto Sans", "DejaVu Sans", "Arial")
                            if f in fams), "TkDefaultFont")
        for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont"):
            tkfont.nametofont(name).configure(family=self.family, size=10)

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.map("Treeview", foreground=_fixed_map(self.style, "foreground"),
                       background=_fixed_map(self.style, "background"))

        self.cash_var = tk.StringVar()
        self.fee_var = tk.StringVar(value="5.00")
        self.lots_var = tk.StringVar(value="1, 10, 100")
        self.tol_var = tk.StringVar(value="0")
        self.algo_var = tk.StringVar(value="A* (recommended)")
        self.limit_var = tk.StringVar(value="3000000")
        for v in (self.cash_var,):
            v.trace_add("write", lambda *a: self.update_totals())

        self._build()
        self.apply_theme("light")
        self.load_example()

    # ---- theming -----------------------------------------------------------
    def apply_theme(self, mode):
        self.mode = mode
        t = self.t = PALETTES[mode]
        s, fam = self.style, self.family
        self.root.configure(bg=t["bg"])
        self.root.option_add("*TCombobox*Listbox.background", t["input"])
        self.root.option_add("*TCombobox*Listbox.foreground", t["text"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", t["accent"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", t["accent_fg"])
        self.root.option_add("*TCombobox*Listbox.font", (fam, 10))

        s.configure("TFrame", background=t["bg"])
        s.configure("Card.TFrame", background=t["card"])
        s.configure("Chip.TFrame", background=t["chip"])
        s.configure("TLabel", background=t["bg"], foreground=t["text"], font=(fam, 10))
        s.configure("Card.TLabel", background=t["card"], foreground=t["text"], font=(fam, 10))
        s.configure("CardTitle.TLabel", background=t["card"], foreground=t["text"], font=(fam, 12, "bold"))
        s.configure("CardSub.TLabel", background=t["card"], foreground=t["muted"], font=(fam, 9))
        s.configure("Field.TLabel", background=t["card"], foreground=t["muted"], font=(fam, 8, "bold"))
        s.configure("Muted.TLabel", background=t["card"], foreground=t["muted"], font=(fam, 10))
        s.configure("Status.TLabel", background=t["bg"], foreground=t["muted"], font=(fam, 10))
        s.configure("Foot.TLabel", background=t["card"], foreground=t["muted"], font=(fam, 9))
        s.configure("FootBad.TLabel", background=t["card"], foreground=t["sell_fg"], font=(fam, 9, "bold"))
        s.configure("ChipValue.TLabel", background=t["chip"], foreground=t["text"], font=(fam, 17, "bold"))
        s.configure("ChipCap.TLabel", background=t["chip"], foreground=t["muted"], font=(fam, 9))
        s.configure("Del.TLabel", background=t["card"], foreground=t["muted"], font=(fam, 10))
        s.configure("DelHover.TLabel", background=t["card"], foreground=t["sell_fg"], font=(fam, 10, "bold"))
        s.configure("Mono.TLabel", background=t["card"], foreground=t["text"], font=("Courier New" if self.family != "DejaVu Sans" else "DejaVu Sans Mono", 10))
        for name, col in (("Ok", t["buy_fg"]), ("Bad", t["sell_fg"]), ("Warn", t["warn"]),
                          ("Info", t["muted"])):
            s.configure(f"{name}.TLabel", background=t["card"], foreground=col, font=(fam, 11, "bold"))

        for style_name, kw in (
            ("TEntry", dict(fieldbackground=t["input"], foreground=t["text"], insertcolor=t["text"],
                            bordercolor=t["border"], lightcolor=t["border"], darkcolor=t["border"],
                            padding=(7, 5), selectbackground=t["accent"], selectforeground=t["accent_fg"])),
            ("TCombobox", dict(fieldbackground=t["input"], background=t["btn"], foreground=t["text"],
                               arrowcolor=t["muted"], bordercolor=t["border"], lightcolor=t["border"],
                               darkcolor=t["border"], padding=(7, 5), selectbackground=t["input"],
                               selectforeground=t["text"])),
        ):
            s.configure(style_name, **kw)
        for st in ("TEntry", "TCombobox"):
            s.map(st, bordercolor=[("focus", t["accent"])], lightcolor=[("focus", t["accent"])],
                  darkcolor=[("focus", t["accent"])])
        s.map("TCombobox", fieldbackground=[("readonly", t["input"])],
              foreground=[("readonly", t["text"])], background=[("active", t["btn_hover"])])

        s.configure("TButton", background=t["btn"], foreground=t["text"], bordercolor=t["border"],
                    lightcolor=t["btn"], darkcolor=t["btn"], focuscolor=t["btn"],
                    padding=(14, 8), font=(fam, 10), relief="flat")
        s.map("TButton", background=[("active", t["btn_hover"]), ("disabled", t["btn"])],
              foreground=[("disabled", t["disabled"])])
        s.configure("Small.TButton", padding=(10, 4), font=(fam, 9))
        s.configure("Accent.TButton", background=t["accent"], foreground=t["accent_fg"],
                    bordercolor=t["accent"], lightcolor=t["accent"], darkcolor=t["accent"],
                    focuscolor=t["accent"], padding=(20, 9), font=(fam, 11, "bold"))
        s.map("Accent.TButton", background=[("active", t["accent_hover"]), ("disabled", t["disabled"])],
              foreground=[("disabled", "#E5E7EB")])

        s.configure("Card.TCheckbutton", background=t["card"], foreground=t["text"],
                    indicatorbackground=t["input"], indicatorforeground=t["accent_fg"],
                    bordercolor=t["border"], focuscolor=t["card"])
        s.map("Card.TCheckbutton", background=[("active", t["card"])],
              indicatorbackground=[("selected", t["accent"]), ("active", t["btn_hover"])])

        s.configure("Treeview", background=t["card"], fieldbackground=t["card"], foreground=t["text"],
                    rowheight=30, borderwidth=0, font=(fam, 10),
                    bordercolor=t["card"], lightcolor=t["card"], darkcolor=t["card"])
        s.map("Treeview", background=[("selected", t["sel"])], foreground=[("selected", t["text"])])
        s.configure("Treeview.Heading", background=t["chip"], foreground=t["muted"], relief="flat",
                    font=(fam, 9, "bold"), padding=(8, 7), borderwidth=0)
        s.map("Treeview.Heading", background=[("active", t["chip"])])
        s.configure("Vertical.TScrollbar", background=t["border"], troughcolor=t["card"],
                    bordercolor=t["card"], arrowcolor=t["muted"], lightcolor=t["border"],
                    darkcolor=t["border"], gripcount=0)
        s.map("Vertical.TScrollbar", background=[("active", t["muted"])])
        s.configure("Accent.Horizontal.TProgressbar", background=t["accent"], troughcolor=t["chip"],
                    bordercolor=t["bg"], lightcolor=t["accent"], darkcolor=t["accent"], thickness=6)

        self.tree.tag_configure("buy", background=t["buy_bg"], foreground=t["text"])
        self.tree.tag_configure("sell", background=t["sell_bg"], foreground=t["text"])
        for fn in self.themed:
            fn(t)
        self.mode_lbl.configure(text="☀  Light mode" if mode == "dark" else "☾  Dark mode")

    def toggle_theme(self):
        self.apply_theme("dark" if self.mode == "light" else "light")

    # ---- layout ------------------------------------------------------------
    def _build(self):
        root = self.root

        # header bar
        header = tk.Frame(root, bd=0)
        header.pack(fill="x")
        title = tk.Label(header, text="Trade Planner", font=(self.family, 20, "bold"), bd=0)
        title.pack(side="left", padx=(24, 0), pady=(14, 14))
        sub = tk.Label(header, text="Cheapest sequence of trades from your portfolio to your goal",
                       font=(self.family, 10), bd=0)
        sub.pack(side="left", padx=(16, 0), pady=(10, 0))
        self.mode_lbl = tk.Label(header, text="", font=(self.family, 10, "bold"), cursor="hand2", bd=0)
        self.mode_lbl.pack(side="right", padx=24)
        self.mode_lbl.bind("<Button-1>", lambda e: self.toggle_theme())

        def theme_header(t):
            header.configure(bg=t["header"])
            for w in (title, self.mode_lbl):
                w.configure(bg=t["header"], fg=t["header_fg"])
            sub.configure(bg=t["header"], fg="#C7D2FE")
        self.themed.append(theme_header)

        body = ttk.Frame(root)
        body.pack(fill="both", expand=True, padx=20, pady=16)
        body.columnconfigure(0, weight=1)
        body.rowconfigure(3, weight=1)

        # settings card
        sc = Card(body, self)
        sc.grid(row=0, column=0, sticky="ew")
        sf = sc.body
        fields = [
            ("Cash on hand ($)", self.cash_var, 14, None),
            ("Fee per trade ($)", self.fee_var, 9, None),
            ("Lot sizes", self.lots_var, 12, None),
            ("Goal tolerance (± %)", self.tol_var, 9, None),
            ("Algorithm", self.algo_var, 20, ["A* (recommended)", "Breadth-first search"]),
            ("Node limit", self.limit_var, 11, None),
        ]
        for c, (label, var, width, choices) in enumerate(fields):
            ttk.Label(sf, text=label.upper(), style="Field.TLabel").grid(
                row=0, column=c, sticky="w", padx=(0, 14), pady=(0, 4))
            if choices:
                w = ttk.Combobox(sf, textvariable=var, values=choices, state="readonly", width=width)
            else:
                w = ttk.Entry(sf, textvariable=var, width=width)
            w.grid(row=1, column=c, sticky="ew", padx=(0, 14))
            sf.columnconfigure(c, weight=1)

        # portfolio cards
        mid = ttk.Frame(body)
        mid.grid(row=1, column=0, sticky="ew", pady=14)
        mid.columnconfigure(0, weight=1, uniform="half")
        mid.columnconfigure(1, weight=1, uniform="half")

        cur = Card(mid, self, "Current portfolio", "what you hold today")
        cur.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        self.cur_table = RowTable(cur.body, self, [("Symbol", "text", 8), ("Shares", "text", 8),
                                                   ("Price ($)", "text", 9), ("Sell-only", "check", 8)],
                                  on_change=self.update_totals)
        self.cur_table.pack(fill="both", expand=True)
        foot = ttk.Frame(cur.body, style="Card.TFrame")
        foot.pack(fill="x", pady=(8, 0))
        ttk.Button(foot, text="＋  Add stock", style="Small.TButton",
                   command=lambda: self.cur_table.add_row()).pack(side="left")
        self.cur_total = ttk.Label(foot, text="", style="Foot.TLabel")
        self.cur_total.pack(side="right")

        goal = Card(mid, self, "Goal portfolio", "stocks left out are sold to 0")
        goal.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        self.goal_table = RowTable(goal.body, self, [("Symbol", "text", 8), ("Target shares", "text", 9),
                                                     ("Price ($) new only", "text", 10),
                                                     ("Sell-only", "check", 8)],
                                   on_change=self.update_totals)
        self.goal_table.pack(fill="both", expand=True)
        foot = ttk.Frame(goal.body, style="Card.TFrame")
        foot.pack(fill="x", pady=(8, 0))
        ttk.Button(foot, text="＋  Add stock", style="Small.TButton",
                   command=lambda: self.goal_table.add_row()).pack(side="left")
        ttk.Button(foot, text="Copy current → goal", style="Small.TButton",
                   command=self.copy_current_to_goal).pack(side="left", padx=8)
        self.goal_total = ttk.Label(foot, text="", style="Foot.TLabel")
        self.goal_total.pack(side="right")

        # action bar
        bar = ttk.Frame(body)
        bar.grid(row=2, column=0, sticky="ew")
        self.solve_btn = ttk.Button(bar, text="Find cheapest trades  ▶", style="Accent.TButton",
                                    command=self.on_solve)
        self.solve_btn.pack(side="left")
        self.cancel_btn = ttk.Button(bar, text="Cancel", command=self.cancel_event.set, state="disabled")
        self.cancel_btn.pack(side="left", padx=(10, 0))
        ttk.Button(bar, text="Load example", command=self.load_example).pack(side="left", padx=(10, 0))
        self.progress = ttk.Progressbar(bar, mode="indeterminate", length=160,
                                        style="Accent.Horizontal.TProgressbar")
        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(bar, textvariable=self.status_var, style="Status.TLabel").pack(side="right")

        # results card
        rc = Card(body, self, "Trade plan")
        rc.grid(row=3, column=0, sticky="nsew", pady=(14, 0))
        rb = rc.body
        top = ttk.Frame(rb, style="Card.TFrame")
        top.pack(fill="x")
        self.banner = ttk.Label(top, text="", style="Info.TLabel")
        self.banner.pack(side="left")

        chips = ttk.Frame(rb, style="Card.TFrame")
        chips.pack(fill="x", pady=(10, 10))
        self.chip_vars = {}
        for i, (key, cap) in enumerate((("trades", "TRADES"), ("fees", "TOTAL FEES"),
                                        ("nodes", "NODES EXPANDED"), ("time", "SEARCH TIME"))):
            chips.columnconfigure(i, weight=1, uniform="chip")
            f = ttk.Frame(chips, style="Chip.TFrame")
            f.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 6, 0 if i == 3 else 6))
            v = tk.StringVar(value="—")
            self.chip_vars[key] = v
            ttk.Label(f, textvariable=v, style="ChipValue.TLabel").pack(anchor="w", padx=14, pady=(10, 0))
            ttk.Label(f, text=cap, style="ChipCap.TLabel").pack(anchor="w", padx=14, pady=(0, 10))

        self.detail = ttk.Label(rb, text="", style="Mono.TLabel", justify="left")
        self.detail.pack(anchor="w", pady=(0, 10))

        wrap = ttk.Frame(rb, style="Card.TFrame")
        wrap.pack(fill="both", expand=True)
        cols = ("#", "Action", "Stock", "Shares", "Price", "Trade value", "Fee", "Cash after", "Holdings after")
        self.tree = ttk.Treeview(wrap, columns=cols, show="headings", height=6, selectmode="browse")
        widths = (44, 90, 80, 80, 90, 130, 80, 120, 360)
        for c, w in zip(cols, widths):
            left = c in ("Action", "Stock", "Holdings after")
            self.tree.heading(c, text=c.upper(), anchor="w" if left else "e")
            self.tree.column(c, width=w, minwidth=40, anchor="w" if left else "e",
                             stretch=(c == "Holdings after"))
        vs = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vs.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vs.pack(side="left", fill="y")
        self.placeholder = ttk.Label(wrap, text="Enter your portfolios and press “Find cheapest trades”.",
                                     style="Muted.TLabel")
        self.placeholder.place(relx=0.5, rely=0.5, anchor="center")


    # ---- helpers -----------------------------------------------------------
    def load_example(self):
        self.cash_var.set("2000.00")
        self.fee_var.set("5.00")
        self.lots_var.set("1, 10, 100")
        self.tol_var.set("0")
        self.cur_table.clear()
        self.goal_table.clear()
        for r in [["AAPL", "50", "180.00", False],
                  ["TSLA", "20", "250.00", False],
                  ["GE", "30", "12.00", True]]:
            self.cur_table.add_row(r, notify=False)
        for r in [["AAPL", "20", "", False],
                  ["TSLA", "0", "", False],
                  ["GE", "0", "", False],
                  ["JNJ", "37", "155.00", False]]:
            self.goal_table.add_row(r, notify=False)
        self.update_totals()

    def copy_current_to_goal(self):
        rows = self.cur_table.values()
        self.goal_table.clear()
        for sym, qty, price, so in rows:
            self.goal_table.add_row([sym, qty, "", so], notify=False)
        self.update_totals()

    def update_totals(self):
        """Live value read-outs under the two tables (silently ignores half-typed rows)."""
        try:
            prices, holdings_val = {}, 0
            for sym, qty, price, _ in self.cur_table.values():
                try:
                    p = to_cents(price)
                    prices[sym.strip().upper()] = p
                    holdings_val += int(qty) * p
                except (ValueError, TypeError):
                    pass
            try:
                cash = to_cents(self.cash_var.get())
            except ValueError:
                cash = 0
            wealth = holdings_val + cash
            self.cur_total.configure(
                text=f"Holdings {money(holdings_val)}  ·  Cash {money(cash)}  ·  Total {money(wealth)}")
            goal_val = 0
            for sym, qty, price, _ in self.goal_table.values():
                try:
                    p = to_cents(price) if str(price).strip() else prices[sym.strip().upper()]
                    goal_val += int(qty) * p
                except (ValueError, KeyError, TypeError):
                    pass
            self.goal_total.configure(
                text=f"Goal value ≈ {money(goal_val)}",
                style="FootBad.TLabel" if goal_val > wealth else "Foot.TLabel")
            if goal_val > wealth:
                self.goal_total.configure(text=f"Goal value ≈ {money(goal_val)}  (exceeds your total!)")
        except Exception:
            pass

    def _set_banner(self, text, kind):
        self.banner.configure(text=text, style=f"{kind}.TLabel")

    # ---- input parsing -----------------------------------------------------
    def build_problem(self) -> Problem:
        def parse_int(txt, what, minimum=0):
            try:
                v = int(str(txt).strip())
            except ValueError:
                raise ValueError(f"{what}: '{txt}' is not a whole number")
            if v < minimum:
                raise ValueError(f"{what} must be at least {minimum}")
            return v

        cash = to_cents(self.cash_var.get())
        if cash < 0:
            raise ValueError("Cash cannot be negative")
        fee = to_cents(self.fee_var.get())
        if fee < 0:
            raise ValueError("Fee cannot be negative")
        try:
            lots = tuple(sorted({int(x) for x in self.lots_var.get().replace(";", ",").split(",") if x.strip()}))
        except ValueError:
            raise ValueError("Lot sizes must be whole numbers separated by commas, e.g. 1, 10, 100")
        if not lots or lots[0] < 1:
            raise ValueError("Lot sizes must be positive whole numbers")
        try:
            tol = Decimal(self.tol_var.get().strip() or "0")
        except InvalidOperation:
            raise ValueError("Tolerance must be a number (percent)")
        if not (0 <= tol < 100):
            raise ValueError("Tolerance must be between 0 and 100 (%)")

        prices: Dict[str, int] = {}
        sell_only: Dict[str, bool] = {}
        start: Dict[str, int] = {}
        order: List[str] = []

        for sym, qty, price, so in self.cur_table.values():
            sym = sym.strip().upper()
            if not sym and not str(qty).strip() and not str(price).strip():
                continue
            if not sym:
                raise ValueError("Current portfolio: a row is missing its symbol")
            if sym in start:
                raise ValueError(f"Current portfolio: {sym} is listed twice")
            start[sym] = parse_int(qty, f"Current portfolio {sym} shares")
            p = to_cents(price) if str(price).strip() else None
            if p is None or p <= 0:
                raise ValueError(f"Current portfolio: {sym} needs a price above $0")
            prices[sym] = p
            sell_only[sym] = bool(so)
            order.append(sym)

        targets: Dict[str, int] = {}
        for sym, qty, price, so in self.goal_table.values():
            sym = sym.strip().upper()
            if not sym and not str(qty).strip() and not str(price).strip():
                continue
            if not sym:
                raise ValueError("Goal: a row is missing its symbol")
            if sym in targets:
                raise ValueError(f"Goal: {sym} is listed twice")
            targets[sym] = parse_int(qty, f"Goal {sym} shares")
            if str(price).strip():
                gp = to_cents(price)
                if gp <= 0:
                    raise ValueError(f"Goal: {sym} price must be above $0")
                if sym in prices and prices[sym] != gp:
                    raise ValueError(f"{sym} has two different prices "
                                     f"({money(prices[sym])} vs {money(gp)}). "
                                     "Prices are fixed - use one price per stock.")
                prices[sym] = gp
            elif sym not in prices:
                raise ValueError(f"Goal: {sym} is a new stock - please enter its price")
            if so:
                sell_only[sym] = True
            sell_only.setdefault(sym, False)
            if sym not in start:
                start[sym] = 0
                order.append(sym)
        if not order:
            raise ValueError("Enter at least one stock")

        bands = [make_band(targets.get(sym, 0), tol) for sym in order]

        return Problem(
            symbols=order,
            prices=[prices[s] for s in order],
            sell_only=[sell_only[s] for s in order],
            start_holdings=tuple(start[s] for s in order),
            start_cash=cash,
            bands=bands,
            lots=lots,
            fee=fee,
        )

    # ---- solving -----------------------------------------------------------
    def on_solve(self):
        try:
            self.problem = self.build_problem()
            limit = int(self.limit_var.get().replace(",", ""))
            if limit < 1:
                raise ValueError
        except ValueError as e:
            messagebox.showerror("Check your input", str(e) or "Node limit must be a positive whole number")
            return

        for item in self.tree.get_children():
            self.tree.delete(item)
        for v in self.chip_vars.values():
            v.set("—")
        self.detail.configure(text="")
        self.placeholder.place_forget()
        self._set_banner("Searching…", "Info")
        self.cancel_event.clear()
        self.solve_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.progress.pack(side="left", padx=(16, 0))
        self.progress.start(12)
        self.status_var.set("")
        algo = "astar" if self.algo_var.get().startswith("A*") else "bfs"
        problem = self.problem

        def work():
            try:
                res = Solver(problem).solve(algo, limit, self.cancel_event,
                                            lambda n: self.q.put(("progress", n)))
                self.q.put(("done", res, algo))
            except Exception as exc:  # pragma: no cover
                self.q.put(("error", repr(exc)))

        threading.Thread(target=work, daemon=True).start()
        self.root.after(80, self.poll)

    def poll(self):
        finished = False
        try:
            while True:
                msg = self.q.get_nowait()
                if msg[0] == "progress":
                    self.status_var.set(f"{msg[1]:,} nodes expanded…")
                elif msg[0] == "done":
                    self.show_result(msg[1], msg[2])
                    finished = True
                elif msg[0] == "error":
                    self._set_banner("Something went wrong", "Bad")
                    messagebox.showerror("Error", msg[1])
                    finished = True
        except queue.Empty:
            pass
        if finished:
            self.progress.stop()
            self.progress.pack_forget()
            self.solve_btn.configure(state="normal")
            self.cancel_btn.configure(state="disabled")
        else:
            self.root.after(80, self.poll)

    # ---- output ------------------------------------------------------------
    def fmt_holdings(self, holdings):
        p = self.problem
        parts = [f"{s} {h}" for s, h in zip(p.symbols, holdings) if h]
        return "  ·  ".join(parts) if parts else "(no stocks)"

    def show_result(self, res: Result, algo: str):
        p = self.problem
        self.chip_vars["nodes"].set(f"{res.expanded:,}")
        self.chip_vars["time"].set(f"{res.seconds:.2f}s")
        self.status_var.set("A* search" if algo == "astar" else "Breadth-first search")

        if res.status != "solved":
            titles = {"no_solution": ("✕  No plan exists", "Bad"),
                      "limit": ("⚠  Search stopped at the node limit", "Warn"),
                      "cancelled": ("Cancelled", "Info")}
            text, kind = titles[res.status]
            self._set_banner(text, kind)
            self.detail.configure(text=res.message)
            self.placeholder.configure(text="No trades to show.")
            self.placeholder.place(relx=0.5, rely=0.5, anchor="center")
            return

        holdings, cash = p.start_holdings, p.start_cash
        for step, mv in enumerate(res.moves, start=1):
            price = p.prices[mv.stock]
            value = mv.lot * price
            i = mv.stock
            if mv.kind == "BUY":
                cash -= value + p.fee
                holdings = holdings[:i] + (holdings[i] + mv.lot,) + holdings[i + 1:]
            else:
                cash += value - p.fee
                holdings = holdings[:i] + (holdings[i] - mv.lot,) + holdings[i + 1:]
            assert cash >= 0 and min(holdings) >= 0
            self.tree.insert("", "end", tags=(mv.kind.lower(),), values=(
                step, ("▲ BUY" if mv.kind == "BUY" else "▼ SELL"), p.symbols[i], mv.lot,
                money(price), money(value), money(p.fee), money(cash),
                "  ·  ".join(f"{s} {h}" for s, h in zip(p.symbols, holdings) if h) or "(none)"))

        n = len(res.moves)
        self.chip_vars["trades"].set(str(n))
        self.chip_vars["fees"].set(money(n * p.fee))
        if n == 0:
            self._set_banner("✓  You already hold the goal portfolio - no trades needed", "Ok")
            self.placeholder.configure(text="No trades needed.")
            self.placeholder.place(relx=0.5, rely=0.5, anchor="center")
        else:
            self._set_banner("✓  Optimal plan found", "Ok")
        lines = [f"Start   {self.fmt_holdings(p.start_holdings)}    cash {money(p.start_cash)}",
                 f"End     {self.fmt_holdings(holdings)}    cash {money(cash)}"]
        if any(lo != hi for lo, hi in p.bands):
            lines.append("Bands   " + "  ·  ".join(
                f"{s} {lo}–{hi}" for s, (lo, hi) in zip(p.symbols, p.bands) if hi > 0))
        self.detail.configure(text="\n".join(lines))


def main():
    if tk is None:
        raise SystemExit("tkinter is not available in this Python installation.")
    root = tk.Tk()
    TradePlannerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()