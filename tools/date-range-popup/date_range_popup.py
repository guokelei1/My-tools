from __future__ import annotations

import argparse
import calendar
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk


WINDOW_TITLE = "Quota Checker"
PERIOD_START = "2026-03-25"
PERIOD_END = "2026-04-24"
DAILY_LIMIT = 50.0
WEEKLY_LIMIT = 250.0
TOTAL_LIMIT = 900.0
WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DATA_FILE = Path(__file__).with_name("usage-data.json")


@dataclass(frozen=True)
class CalendarDay:
    value: date
    actual_spend: float | None
    forecast_spend: float | None
    status: str

    @property
    def label(self) -> str:
        return self.value.strftime("%Y-%m-%d")

    @property
    def weekday_label(self) -> str:
        return WEEKDAY_NAMES[self.value.weekday()]


@dataclass(frozen=True)
class PlanResult:
    period_start: date
    period_end: date
    today: date
    usage_file: Path
    used_total: float
    used_this_week: float
    exact_hit_average_daily: float | None
    exact_hit_average_feasible: bool
    max_flat_daily_allowed: float
    max_future_additional: float
    max_final_total: float
    wasted_amount: float
    remaining_days: int
    calendar_days: list[CalendarDay]


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def date_key(value: date) -> str:
    return value.strftime("%Y-%m-%d")


def round_money(value: float) -> float:
    return round(value + 1e-9, 2)


def format_amount(value: float) -> str:
    rounded = round_money(value)
    if abs(rounded - round(rounded)) < 1e-9:
        return str(int(round(rounded)))
    return f"{rounded:.2f}".rstrip("0").rstrip(".")


def format_average(value: float) -> str:
    rounded = round(value + 1e-9, 4)
    if abs(rounded - round(rounded)) < 1e-9:
        return str(int(round(rounded)))
    return f"{rounded:.4f}".rstrip("0").rstrip(".")


def week_start(value: date) -> date:
    return value - timedelta(days=value.weekday())


def list_days(start_day: date, end_day: date) -> list[date]:
    if start_day > end_day:
        return []

    days: list[date] = []
    current_day = start_day
    while current_day <= end_day:
        days.append(current_day)
        current_day += timedelta(days=1)
    return days


def months_in_range(start_day: date, end_day: date) -> list[tuple[int, int]]:
    months: list[tuple[int, int]] = []
    year = start_day.year
    month = start_day.month

    while (year, month) <= (end_day.year, end_day.month):
        months.append((year, month))
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1

    return months


def build_usage_template() -> dict[date, float | None]:
    period_start = parse_date(PERIOD_START)
    period_end = parse_date(PERIOD_END)
    return {current_day: None for current_day in list_days(period_start, period_end)}


def save_usage_file(path: Path, usage_by_day: dict[date, float | None]) -> None:
    ordered_daily_usage = {date_key(day): usage_by_day[day] for day in sorted(usage_by_day)}
    payload = {"daily_usage": ordered_daily_usage}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def ensure_usage_file(path: Path) -> None:
    if path.exists():
        return

    save_usage_file(path, build_usage_template())


def load_usage_file(path: Path) -> dict[date, float | None]:
    ensure_usage_file(path)

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path.name}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"{path.name} must contain a JSON object")

    raw_daily_usage = data.get("daily_usage", {})
    if not isinstance(raw_daily_usage, dict):
        raise ValueError(f"{path.name}: daily_usage must be an object")

    normalized_usage = build_usage_template()

    for key, raw_value in raw_daily_usage.items():
        if not isinstance(key, str):
            raise ValueError(f"{path.name}: date keys must be strings")

        try:
            usage_day = parse_date(key)
        except ValueError as exc:
            raise ValueError(f"{path.name}: invalid date key {key!r}, expected YYYY-MM-DD") from exc

        if usage_day not in normalized_usage:
            continue

        if raw_value is None or raw_value == "":
            normalized_usage[usage_day] = None
            continue

        try:
            amount = round_money(float(raw_value))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{path.name}: invalid amount for {key!r}") from exc

        if amount < 0:
            raise ValueError(f"{path.name}: amount for {key!r} cannot be negative")
        if amount > DAILY_LIMIT:
            raise ValueError(f"{path.name}: amount for {key!r} cannot exceed daily limit ${format_amount(DAILY_LIMIT)}")

        normalized_usage[usage_day] = amount

    save_usage_file(path, normalized_usage)
    return normalized_usage


def validate_actual_usage(
    usage_by_day: dict[date, float | None],
    today: date,
    period_start: date,
    period_end: date,
) -> None:
    relevant_days = [
        day
        for day, amount in usage_by_day.items()
        if amount is not None and period_start <= day <= min(today, period_end)
    ]

    total_used = round_money(sum(float(usage_by_day[day]) for day in relevant_days))
    if total_used > TOTAL_LIMIT:
        raise ValueError(f"Recorded usage already exceeds total limit ${format_amount(TOTAL_LIMIT)}")

    weekly_totals: dict[date, float] = {}
    for usage_day in relevant_days:
        key = week_start(usage_day)
        amount = float(usage_by_day[usage_day])
        weekly_totals[key] = round_money(weekly_totals.get(key, 0.0) + amount)

    for key, weekly_total in weekly_totals.items():
        if weekly_total > WEEKLY_LIMIT:
            raise ValueError(
                f"Recorded usage for week starting {date_key(key)} exceeds weekly limit ${format_amount(WEEKLY_LIMIT)}"
            )


def compute_actual_usage(
    usage_by_day: dict[date, float | None],
    today: date,
    period_start: date,
    period_end: date,
) -> tuple[dict[date, float], float, float]:
    actual_by_day: dict[date, float] = {}
    last_actual_day = min(today, period_end)

    if period_start <= last_actual_day:
        for current_day in list_days(period_start, last_actual_day):
            amount = usage_by_day.get(current_day)
            if amount is not None:
                actual_by_day[current_day] = round_money(amount)

    used_total = round_money(sum(actual_by_day.values()))

    used_this_week = 0.0
    current_week_start = week_start(today)
    for usage_day, amount in actual_by_day.items():
        if current_week_start <= usage_day <= today:
            used_this_week = round_money(used_this_week + amount)

    return actual_by_day, used_total, used_this_week


def build_forward_max_plan(
    today: date,
    used_total: float,
    used_this_week: float,
    period_start: date,
    period_end: date,
) -> dict[date, float]:
    future_start = max(period_start, today + timedelta(days=1))
    future_days = list_days(future_start, period_end) if future_start <= period_end else []

    remaining_total = round_money(max(0.0, TOTAL_LIMIT - used_total))
    plan: dict[date, float] = {}
    current_week_key: date | None = None
    current_week_used = 0.0

    for future_day in future_days:
        future_week_key = week_start(future_day)
        if future_week_key != current_week_key:
            current_week_key = future_week_key
            if future_week_key == week_start(today) and period_start <= today <= period_end:
                current_week_used = used_this_week
            else:
                current_week_used = 0.0

        weekly_remaining = round_money(max(0.0, WEEKLY_LIMIT - current_week_used))

        if remaining_total <= 0.0 or weekly_remaining <= 0.0:
            spend = 0.0
        else:
            spend = round_money(min(DAILY_LIMIT, weekly_remaining, remaining_total))

        plan[future_day] = spend
        current_week_used = round_money(current_week_used + spend)
        remaining_total = round_money(remaining_total - spend)

    return plan


def compute_exact_hit_average(
    today: date,
    used_total: float,
    used_this_week: float,
    period_start: date,
    period_end: date,
) -> tuple[float | None, bool, float]:
    future_start = max(period_start, today + timedelta(days=1))
    future_days = list_days(future_start, period_end) if future_start <= period_end else []
    remaining_total = round_money(max(0.0, TOTAL_LIMIT - used_total))

    if not future_days:
        if remaining_total <= 0.0:
            return 0.0, True, 0.0
        return None, False, 0.0

    required_average = remaining_total / len(future_days)
    max_flat_daily_allowed = DAILY_LIMIT

    days_per_week: dict[date, int] = {}
    for future_day in future_days:
        key = week_start(future_day)
        days_per_week[key] = days_per_week.get(key, 0) + 1

    current_week_key = week_start(today)
    for week_key, day_count in days_per_week.items():
        weekly_capacity = WEEKLY_LIMIT
        if week_key == current_week_key and period_start <= today <= period_end:
            weekly_capacity = round_money(max(0.0, WEEKLY_LIMIT - used_this_week))

        max_flat_daily_allowed = min(max_flat_daily_allowed, weekly_capacity / day_count)

    max_flat_daily_allowed = round(max_flat_daily_allowed + 1e-9, 4)
    feasible = required_average <= max_flat_daily_allowed + 1e-9 and required_average <= DAILY_LIMIT + 1e-9
    return required_average, feasible, max_flat_daily_allowed


def compute_plan(today: date, usage_by_day: dict[date, float | None]) -> PlanResult:
    period_start = parse_date(PERIOD_START)
    period_end = parse_date(PERIOD_END)

    if period_start > period_end:
        raise ValueError("PERIOD_START cannot be later than PERIOD_END")

    validate_actual_usage(usage_by_day, today, period_start, period_end)
    actual_by_day, used_total, used_this_week = compute_actual_usage(usage_by_day, today, period_start, period_end)
    future_plan = build_forward_max_plan(today, used_total, used_this_week, period_start, period_end)
    exact_hit_average_daily, exact_hit_average_feasible, max_flat_daily_allowed = compute_exact_hit_average(
        today,
        used_total,
        used_this_week,
        period_start,
        period_end,
    )

    calendar_days: list[CalendarDay] = []
    for current_day in list_days(period_start, period_end):
        if current_day <= today:
            actual_spend = actual_by_day.get(current_day)
            calendar_days.append(
                CalendarDay(
                    value=current_day,
                    actual_spend=actual_spend,
                    forecast_spend=None,
                    status="actual" if actual_spend is not None else "empty",
                )
            )
        else:
            forecast_spend = future_plan.get(current_day, 0.0)
            calendar_days.append(
                CalendarDay(
                    value=current_day,
                    actual_spend=None,
                    forecast_spend=forecast_spend,
                    status="forecast" if forecast_spend > 0 else "paused",
                )
            )

    max_future_additional = round_money(sum(future_plan.values()))
    max_final_total = round_money(min(TOTAL_LIMIT, used_total + max_future_additional))
    wasted_amount = round_money(max(0.0, TOTAL_LIMIT - max_final_total))
    remaining_days = sum(1 for day in calendar_days if day.value > today)

    return PlanResult(
        period_start=period_start,
        period_end=period_end,
        today=today,
        usage_file=DATA_FILE,
        used_total=used_total,
        used_this_week=used_this_week,
        exact_hit_average_daily=exact_hit_average_daily,
        exact_hit_average_feasible=exact_hit_average_feasible,
        max_flat_daily_allowed=max_flat_daily_allowed,
        max_future_additional=max_future_additional,
        max_final_total=max_final_total,
        wasted_amount=wasted_amount,
        remaining_days=remaining_days,
        calendar_days=calendar_days,
    )


def build_status_lines(result: PlanResult) -> list[str]:
    lines = [
        f"Period: {date_key(result.period_start)} to {date_key(result.period_end)}",
        f"Today (end of day): {date_key(result.today)}",
        f"Usage file: {result.usage_file.name}",
        f"Rules: daily ${format_amount(DAILY_LIMIT)}, weekly ${format_amount(WEEKLY_LIMIT)} reset on Monday, total ${format_amount(TOTAL_LIMIT)}",
        f"Only filled values in the JSON count as actual usage; fill 0 for completed zero-use days",
        f"Actual used so far: ${format_amount(result.used_total)}",
        f"Actual used this week: ${format_amount(result.used_this_week)}",
        f"Remaining future days: {result.remaining_days}",
        f"If you max out every remaining day, future additional use = ${format_amount(result.max_future_additional)}",
        f"Max final total by {date_key(result.period_end)} = ${format_amount(result.max_final_total)}",
        f"Unavoidable unused quota = ${format_amount(result.wasted_amount)}",
    ]

    if result.exact_hit_average_daily is None:
        lines.append("Exact-hit flat daily average: impossible because no future days remain")
    else:
        lines.append(
            f"Exact-hit flat daily average to end at ${format_amount(TOTAL_LIMIT)} = ${format_average(result.exact_hit_average_daily)}"
        )
        if result.exact_hit_average_feasible:
            lines.append("This flat daily average is feasible under the daily and weekly caps")
        else:
            lines.append(
                f"This flat daily average is not feasible; max flat daily amount allowed by the caps is ${format_average(result.max_flat_daily_allowed)}"
            )

    lines.append("Legend: red = actual from file, white = empty / not filled yet, green = future max usage, gray = forced stop / 0")
    return lines


def print_text(result: PlanResult) -> None:
    for line in build_status_lines(result):
        print(line)

    print("-" * 60)
    for day in result.calendar_days:
        if day.status == "actual":
            print(f"{day.label}  {day.weekday_label}  actual ${format_amount(day.actual_spend or 0.0)}")
        elif day.status == "empty":
            print(f"{day.label}  {day.weekday_label}  empty")
        elif day.status == "forecast":
            print(f"{day.label}  {day.weekday_label}  forecast ${format_amount(day.forecast_spend or 0.0)}")
        else:
            print(f"{day.label}  {day.weekday_label}  0")


def create_scrollable_container(root: tk.Tk) -> ttk.Frame:
    container = ttk.Frame(root, padding=12)
    container.pack(fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(container, highlightthickness=0)
    scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)
    content = ttk.Frame(canvas)

    content.bind(
        "<Configure>",
        lambda event: canvas.configure(scrollregion=canvas.bbox("all")),
    )

    canvas.create_window((0, 0), window=content, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def on_mouse_wheel(event: tk.Event) -> None:
        canvas.yview_scroll(int(-event.delta / 120), "units")

    canvas.bind_all("<MouseWheel>", on_mouse_wheel)
    return content


def add_summary(parent: ttk.Frame, result: PlanResult) -> None:
    summary = ttk.LabelFrame(parent, text="Summary", padding=12)
    summary.pack(fill=tk.X, pady=(0, 12))

    ttk.Label(summary, text=WINDOW_TITLE, font=("Microsoft YaHei UI", 16, "bold")).pack(anchor="w")
    for line in build_status_lines(result):
        ttk.Label(summary, text=line, font=("Microsoft YaHei UI", 10)).pack(anchor="w", pady=(4, 0))


def get_day_colors(day: CalendarDay) -> tuple[str, str]:
    if day.status == "actual":
        return "#FECACA", "#7F1D1D"
    if day.status == "empty":
        return "#FFFFFF", "#111827"
    if day.status == "forecast":
        return "#BBF7D0", "#166534"
    return "#E5E7EB", "#374151"


def get_day_cell_text(day: CalendarDay) -> str:
    if day.status == "actual":
        amount_line = f"Actual ${format_amount(day.actual_spend or 0.0)}"
    elif day.status == "empty":
        amount_line = "Empty"
    elif day.status == "forecast":
        amount_line = f"Plan ${format_amount(day.forecast_spend or 0.0)}"
    else:
        amount_line = "0"

    return "\n".join([
        f"{day.value.day:02d}",
        day.weekday_label,
        amount_line,
    ])


def add_month_card(parent: ttk.Frame, year: int, month: int, result: PlanResult, day_map: dict[date, CalendarDay]) -> None:
    card = ttk.LabelFrame(parent, text=f"{year}-{month:02d}", padding=10)
    card.pack(fill=tk.X, expand=True, pady=(0, 12))

    for column_index, weekday_name in enumerate(WEEKDAY_NAMES):
        header = ttk.Label(card, text=weekday_name, anchor="center")
        header.grid(row=0, column=column_index, padx=4, pady=(0, 6), sticky="ew")
        card.columnconfigure(column_index, weight=1)

    month_matrix = calendar.Calendar(firstweekday=0).monthdatescalendar(year, month)

    for row_index, week in enumerate(month_matrix, start=1):
        for column_index, cell_day in enumerate(week):
            if cell_day.month != month or cell_day < result.period_start or cell_day > result.period_end:
                cell = ttk.Label(card, text="", relief=tk.FLAT)
                cell.grid(row=row_index, column=column_index, padx=4, pady=4, sticky="nsew")
                continue

            calendar_day = day_map[cell_day]
            background, foreground = get_day_colors(calendar_day)
            text = get_day_cell_text(calendar_day)

            cell = tk.Label(
                card,
                text=text,
                justify="center",
                bg=background,
                fg=foreground,
                relief=tk.RIDGE,
                bd=1,
                padx=8,
                pady=8,
                font=("Microsoft YaHei UI", 9),
            )
            cell.grid(row=row_index, column=column_index, padx=4, pady=4, sticky="nsew")


def show_popup(result: PlanResult) -> None:
    root = tk.Tk()
    root.title(WINDOW_TITLE)
    root.geometry("980x720")
    root.minsize(820, 540)

    content = create_scrollable_container(root)
    add_summary(content, result)

    day_map = {day.value: day for day in result.calendar_days}
    for year, month in months_in_range(result.period_start, result.period_end):
        add_month_card(content, year, month, result, day_map)

    root.mainloop()


def ask_today(default_today: date) -> date | None:
    root = tk.Tk()
    root.withdraw()

    try:
        while True:
            value = simpledialog.askstring(
                WINDOW_TITLE,
                "Enter today's date (end of day) in YYYY-MM-DD:",
                parent=root,
                initialvalue=date_key(default_today),
            )
            if value is None:
                return None

            try:
                return parse_date(value.strip())
            except ValueError:
                messagebox.showerror("Input error", "Date must use YYYY-MM-DD", parent=root)
    finally:
        root.destroy()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Show actual usage from a local file and forecast the max future usage on a fixed calendar range.")
    parser.add_argument(
        "--today",
        help="Treat the calculation as of the end of this date. Format: YYYY-MM-DD",
    )
    parser.add_argument(
        "--text",
        action="store_true",
        help="Print results in the terminal only.",
    )
    return parser


def report_error(message: str, text_mode: bool) -> int:
    if text_mode:
        print(f"Error: {message}")
        return 1

    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Error", message)
    root.destroy()
    return 1


def main() -> int:
    args = build_parser().parse_args()

    if args.today:
        try:
            today = parse_date(args.today)
        except ValueError:
            return report_error("--today must use YYYY-MM-DD", args.text)
    elif args.text:
        today = date.today()
    else:
        today = ask_today(date.today())
        if today is None:
            return 0

    try:
        usage_by_day = load_usage_file(DATA_FILE)
        result = compute_plan(today, usage_by_day)
    except ValueError as exc:
        return report_error(str(exc), args.text)

    if args.text:
        print_text(result)
        return 0

    show_popup(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
