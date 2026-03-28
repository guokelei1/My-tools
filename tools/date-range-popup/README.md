# date-range-popup

`date-range-popup` is a fixed-range quota calendar.

## Fixed window

- Active period: `2026-03-25` to `2026-04-24`
- Daily limit: `$50`
- Weekly limit: `$250`
- Weekly reset: every Monday
- Total limit: `$900`

## Local usage file

Edit `tools/date-range-popup/usage-data.json`.

The file now includes every date in the active period.

- Use `null` for empty / not filled yet
- Fill a number when that day has already happened
- Fill `0` if that day happened but the actual spend was zero

Example:

```json
{
  "daily_usage": {
    "2026-03-25": 40,
    "2026-03-26": 0,
    "2026-03-27": null
  }
}
```

## What the calendar shows

- Red cell: actual usage from the JSON file
- White cell: date exists in the JSON file but is still empty
- Green cell: future max usage if you keep spending as much as allowed every remaining day
- Gray cell: forced stop day, so the calendar shows `0`

## Extra calculation

The summary panel also shows one more result:

- if you use the same amount every remaining day, what flat daily average would hit `$900` exactly
- whether that flat average is actually feasible under both the daily `$50` cap and the weekly `$250` cap

## Run

Double-click `run-date-range-popup.cmd`.

At startup the tool asks for `today` in `YYYY-MM-DD` format, then it loads `usage-data.json` and renders the calendar.

Terminal mode:

```powershell
python .\date_range_popup.py --today 2026-03-26 --text
```
