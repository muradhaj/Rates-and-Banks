"""Download the latest ECB and Bank of England policy rates and rewrite data/policy_rates.csv.

Runs every day from GitHub Actions (see .github/workflows/update.yml).
Uses only the Python standard library.

Sources:
  ECB deposit facility rate: ECB Data Portal, series FM.D.U2.EUR.4F.KR.DFR.LEV
  Bank of England Bank Rate: BoE Interactive Database, series IUDBEDR

If a download fails or looks wrong, the existing file is kept, so the website never breaks.
"""

import csv
import io
import json
import sys
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

START = date(2015, 1, 1)
ROOT = Path(__file__).resolve().parent.parent
RATES_FILE = ROOT / "data" / "policy_rates.csv"
META_FILE = ROOT / "data" / "meta.json"

ECB_URL = (
    "https://data-api.ecb.europa.eu/service/data/FM/D.U2.EUR.4F.KR.DFR.LEV"
    "?format=csvdata&startPeriod=2014-01-01"
)
BOE_URL = (
    "https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp"
    "?csv.x=yes&Datefrom=01/Jan/2014&Dateto=now&SeriesCodes=IUDBEDR"
    "&CSVF=TN&UsingCodes=Y&VPD=Y&VFD=N"
)
HEADERS = {
    # The Bank of England database refuses requests without a browser-like User-Agent.
    "User-Agent": "Mozilla/5.0 (rates-and-banks dashboard; GitHub Actions)",
    "Accept": "text/csv,text/plain,*/*",
}

DATE_FORMATS = ("%Y-%m-%d", "%d %b %Y", "%d %B %Y", "%d/%m/%Y", "%d-%b-%Y")


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8-sig", errors="replace")


def parse_date(text):
    text = text.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"unknown date format: {text!r}")


def parse_series(text, date_cols, value_cols):
    """Read a CSV and return {date: value}. Column names are matched case-insensitively."""
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError("empty CSV")
    names = {n.strip().upper(): n for n in reader.fieldnames}
    dcol = next((names[c] for c in date_cols if c in names), None)
    vcol = next((names[c] for c in value_cols if c in names), None)
    if dcol is None or vcol is None:
        raise ValueError(f"expected columns not found, got {reader.fieldnames}")
    out = {}
    for row in reader:
        raw_d, raw_v = (row.get(dcol) or "").strip(), (row.get(vcol) or "").strip()
        if not raw_d or not raw_v:
            continue
        try:
            out[parse_date(raw_d)] = float(raw_v)
        except ValueError:
            continue
    return out


def parse_ecb(text):
    return parse_series(text, ["TIME_PERIOD", "DATE"], ["OBS_VALUE", "VALUE"])


def parse_boe(text):
    return parse_series(text, ["DATE"], ["IUDBEDR"])


def check(series, name):
    if len(series) < 100:
        raise ValueError(f"{name}: only {len(series)} observations")
    bad = [v for v in series.values() if not -2 <= v <= 20]
    if bad:
        raise ValueError(f"{name}: implausible values {bad[:3]}")
    latest = max(series)
    if (date.today() - latest).days > 21:
        raise ValueError(f"{name}: latest observation is old ({latest})")


def rate_on(series, day):
    """Rate in force on a day: the last observation on or before it."""
    past = [d for d in series if d <= day]
    return series[max(past)] if past else None


def change_points(ecb, boe, today):
    """Rows for the start date, every date either rate changed, and today."""
    rows = []
    prev = None
    days = sorted(d for d in set(ecb) | set(boe) if d >= START)
    for d in [START] + days:
        cur = (rate_on(ecb, d), rate_on(boe, d))
        if None in cur:
            continue
        if cur != prev:
            rows.append((d, *cur))
            prev = cur
    if rows and rows[-1][0] < today:
        rows.append((today, *prev))
    return rows


def write_rates(rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["date", "ecb_deposit_rate", "boe_bank_rate"])
    for d, e, b in rows:
        w.writerow([d.isoformat(), f"{e:.2f}", f"{b:.2f}"])
    RATES_FILE.write_text(buf.getvalue())


def write_meta(status):
    meta = json.loads(META_FILE.read_text()) if META_FILE.exists() else {}
    meta["rates_checked_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    meta["rates_status"] = status
    if status == "ok":
        meta["rates_updated_at"] = meta["rates_checked_at"]
    META_FILE.write_text(json.dumps(meta, indent=2) + "\n")


def main():
    try:
        ecb = parse_ecb(fetch(ECB_URL))
        check(ecb, "ECB")
        boe = parse_boe(fetch(BOE_URL))
        check(boe, "BoE")
        rows = change_points(ecb, boe, date.today())
        if len(rows) < 10:
            raise ValueError(f"only {len(rows)} rate changes found")
    except Exception as exc:  # keep the old data if anything goes wrong
        print(f"WARNING: rates not updated, keeping existing file. Reason: {exc}", file=sys.stderr)
        write_meta(f"failed: {exc}")
        return 0
    write_rates(rows)
    write_meta("ok")
    print(f"Updated {RATES_FILE.name}: {len(rows)} rows, latest {rows[-1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
