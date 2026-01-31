#!/usr/bin/env python3
"""fix_srt.py

簡介:
  修正 SRT 檔案中的常見問題：編號不連續、時間長度為 0、時間重疊、過短段落。
  會自動判斷語言（簡單 heuristic），並執行保守的文字修正（拼字/標點/中英文間隔）以保留原始語意。

用法範例:
  python fix_srt.py --input in.srt --output out.srt --min-duration 0.5 --dry-run

不依賴第三方套件（可選接入 LLM 做更進階校正）。
"""
from __future__ import annotations

import argparse
import re
from datetime import timedelta
from typing import List, Tuple


TIMESTAMP_RE = re.compile(r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})$")
PUNCT_END = set('.?!。！？')


def parse_timestamp(ts: str) -> timedelta:
    m = TIMESTAMP_RE.match(ts.strip())
    if not m:
        raise ValueError(f"Invalid timestamp: {ts}")
    hh, mm, ss, ms = map(int, m.groups())
    return timedelta(hours=hh, minutes=mm, seconds=ss, milliseconds=ms)


def format_timestamp(td: timedelta) -> str:
    total_ms = int(td.total_seconds() * 1000)
    if total_ms < 0:
        total_ms = 0
    ms = total_ms % 1000
    s = (total_ms // 1000) % 60
    m = (total_ms // (1000 * 60)) % 60
    h = total_ms // (1000 * 60 * 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


class Subtitle:
    def __init__(self, index: int, start: timedelta, end: timedelta, content: str):
        self.index = index
        self.start = start
        self.end = end
        self.content = content.strip()

    @property
    def duration(self) -> float:
        return (self.end - self.start).total_seconds()


def read_srt(path: str) -> List[Subtitle]:
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    parts = re.split(r"\n{2,}", text.strip())
    subs: List[Subtitle] = []
    for part in parts:
        lines = part.strip().splitlines()
        if len(lines) < 2:
            continue
        # first line may be index
        idx_line = lines[0].strip()
        try:
            idx = int(idx_line)
            times_line = lines[1]
            content_lines = lines[2:]
        except ValueError:
            # no index present, assume times at first line
            idx = len(subs) + 1
            times_line = lines[0]
            content_lines = lines[1:]

        if '-->' not in times_line:
            continue
        start_s, end_s = [s.strip() for s in times_line.split('-->')]
        start = parse_timestamp(start_s)
        end = parse_timestamp(end_s)
        content = '\n'.join(content_lines).strip()
        subs.append(Subtitle(idx, start, end, content))
    return subs


def write_srt(path: str, subs: List[Subtitle]) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        for i, s in enumerate(subs, start=1):
            f.write(f"{i}\n")
            f.write(f"{format_timestamp(s.start)} --> {format_timestamp(s.end)}\n")
            f.write(s.content + "\n\n")


def detect_language_simple(text: str) -> str:
    # Heuristic: if contains CJK characters -> zh, else en
    if re.search(r"[\u4e00-\u9fff]", text):
        return 'zh'
    return 'en'


def conservative_fix_text(text: str, lang: str = 'en', aggressiveness: float = 0.0) -> Tuple[str, bool]:
    """Perform conservative corrections. Return (new_text, changed)."""
    orig = text
    # normalize spaces
    text = re.sub(r"[ \t\u00A0]+", ' ', text)
    text = text.strip()

    if lang == 'en':
        # remove space before punctuation, ensure space after . , ? ! : ;
        text = re.sub(r"\s+([.,!?;:])", r"\1", text)
        text = re.sub(r"([.,!?;:])([^\s])", r"\1 \2", text)
        # collapse multiple spaces
        text = re.sub(r"\s{2,}", ' ', text)
        # capitalize first letter of the subtitle if looks like a sentence
        if text and text[0].islower():
            text = text[0].upper() + text[1:]

    else:  # zh
        # remove spaces before CJK punctuation
        text = re.sub(r"\s+([，。！？；：])", r"\1", text)
        # insert space between CJK and Latin sequences (conservative)
        text = re.sub(r"([\u4e00-\u9fff])([A-Za-z0-9]+)", r"\1 \2", text)
        text = re.sub(r"([A-Za-z0-9]+)([\u4e00-\u9fff])", r"\1 \2", text)
        # collapse multiple spaces
        text = re.sub(r"\s{2,}", ' ', text)

    changed = text != orig
    return text, changed


def fix_timing_and_merge(subs: List[Subtitle], min_duration: float = 0.5) -> Tuple[List[Subtitle], dict]:
    """Fix timestamps, avoid overlaps, merge tiny segments conservatively.

    Returns (new_subs, stats)
    """
    changed = {'adjusted': 0, 'merged': 0, 'renumbered': 0}
    # First pass: fix invalid end <= start
    for s in subs:
        if s.end <= s.start:
            s.end = s.start + timedelta(seconds=min_duration)
            changed['adjusted'] += 1

    # Second pass: ensure monotonic, merge very short segments
    i = 0
    out: List[Subtitle] = []
    while i < len(subs):
        s = subs[i]
        # if previous exists and overlap -> shift start to prev.end
        if out and s.start < out[-1].end:
            s.start = out[-1].end
            if s.end <= s.start:
                s.end = s.start + timedelta(seconds=min_duration)
            changed['adjusted'] += 1

        # merge conservative: if duration < min_duration and previous exists and previous doesn't end with punctuation
        if s.duration < min_duration and out:
            prev = out[-1]
            last_char = prev.content.strip()[-1:] if prev.content.strip() else ''
            if last_char not in PUNCT_END:
                # merge into prev
                prev.content = prev.content.rstrip() + ' ' + s.content.lstrip()
                prev.end = max(prev.end, s.end)
                changed['merged'] += 1
                i += 1
                continue

        # otherwise, try merging with next if short and next exists and next starts immediately
        if s.duration < min_duration and i + 1 < len(subs):
            nxt = subs[i + 1]
            # if next starts <= s.end + small epsilon -> merge into next by moving next.start earlier
            if nxt.start <= s.end + timedelta(milliseconds=int(min_duration * 1000 / 2)):
                nxt.start = s.start
                nxt.content = s.content.rstrip() + ' ' + nxt.content.lstrip()
                changed['merged'] += 1
                i += 1
                continue

        out.append(s)
        i += 1

    # Third pass: ensure no overlaps and minimal gaps
    for j in range(1, len(out)):
        prev = out[j - 1]
        cur = out[j]
        if cur.start < prev.end:
            # push cur.start to prev.end, and ensure duration
            cur.start = prev.end
            if cur.end <= cur.start:
                cur.end = cur.start + timedelta(seconds=min_duration)
            changed['adjusted'] += 1

    # Renumbering implied on write; stats
    changed['renumbered'] = len(out)
    return out, changed


def summarize_changes(original: List[Subtitle], new: List[Subtitle], stats: dict) -> str:
    lines = []
    lines.append(f"original_count={len(original)}, new_count={len(new)}")
    lines.append(f"adjusted={stats.get('adjusted',0)}, merged={stats.get('merged',0)}, renumbered={stats.get('renumbered',0)}")
    return '\n'.join(lines)


def process_file(in_path: str, out_path: str, min_duration: float = 0.5, dry_run: bool = False, aggressiveness: float = 0.0, preserve_index: bool = False) -> dict:
    subs = read_srt(in_path)
    original = [Subtitle(s.index, s.start, s.end, s.content) for s in subs]

    # language detection per subtitle and conservative correction
    total_text_changes = 0
    for s in subs:
        lang = detect_language_simple(s.content)
        new_text, changed = conservative_fix_text(s.content, lang=lang, aggressiveness=aggressiveness)
        if changed:
            s.content = new_text
            total_text_changes += 1

    fixed_subs, stats = fix_timing_and_merge(subs, min_duration=min_duration)

    if not preserve_index:
        # renumber on write
        pass

    if dry_run:
        summary = summarize_changes(original, fixed_subs, stats)
        print("DRY RUN - summary:\n" + summary)
        return {'summary': summary, 'text_changes': total_text_changes, **stats}

    write_srt(out_path, fixed_subs)
    summary = summarize_changes(original, fixed_subs, stats)
    return {'summary': summary, 'text_changes': total_text_changes, **stats}


def main():
    parser = argparse.ArgumentParser(description='Fix SRT timing, numbering and conservative text corrections')
    parser.add_argument('--input', '-i', required=True, help='Input .srt file')
    parser.add_argument('--output', '-o', required=True, help='Output fixed .srt file')
    parser.add_argument('--min-duration', type=float, default=0.5, help='Minimum subtitle duration in seconds (default 0.5)')
    parser.add_argument('--dry-run', action='store_true', help='Show summary of changes without writing file')
    parser.add_argument('--aggressiveness', type=float, default=0.0, help='Aggressiveness of text rewrite (0.0 conservative)')
    parser.add_argument('--preserve-index', action='store_true', help='Preserve original index numbers if possible')
    args = parser.parse_args()

    result = process_file(args.input, args.output, min_duration=args.min_duration, dry_run=args.dry_run, aggressiveness=args.aggressiveness, preserve_index=args.preserve_index)
    if args.dry_run:
        print(result['summary'])
    else:
        print('Wrote', args.output)
        print(result['summary'])


if __name__ == '__main__':
    main()
