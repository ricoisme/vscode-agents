#!/usr/bin/env python3
"""
srt_to_vtt.py

簡易且可執行的 SRT -> VTT 轉換程式。
- 自動偵測編碼（若已安裝 chardet）
- 嘗試偵測語言（若已安裝 langdetect）並在檔頭加入 LANG 註記（選用）

用法:
  python srt_to_vtt.py input.srt output.vtt [--encoding ENCODING] [--no-lang]

此檔案盡量不依賴外部套件，但若要更準確的編碼/語言偵測，建議安裝 `chardet` 與 `langdetect`。
"""

from __future__ import annotations
import argparse
import re
import sys
from typing import List, Tuple


def detect_encoding(path: str) -> str:
    try:
        import chardet
    except Exception:
        return 'utf-8'

    with open(path, 'rb') as f:
        raw = f.read()
    res = chardet.detect(raw)
    enc = res.get('encoding')
    return enc or 'utf-8'


def normalize_time(s: str) -> str:
    # SRT uses 00:00:01,234  -> VTT uses 00:00:01.234
    s = s.strip()
    s = s.replace(',', '.')
    # ensure format HH:MM:SS.mmm (pad hours if needed)
    parts = s.split(':')
    if len(parts) == 3:
        hh, mm, ss = parts
        if len(hh) == 1:
            hh = hh.zfill(2)
        # ensure milliseconds have 3 digits
        if '.' in ss:
            sec, ms = ss.split('.')
            ms = (ms + '000')[:3]
            ss = sec + '.' + ms
        else:
            ss = ss + '.000'
        return f"{hh}:{mm}:{ss}"
    return s


def parse_srt(content: str) -> List[Tuple[str, str, str]]:
    # Split blocks by blank lines (handle CRLF)
    blocks = re.split(r'\r?\n\s*\r?\n', content.strip())
    cues = []
    time_re = re.compile(r"(\d{1,2}:\d{2}:\d{2}[,\.]\d{1,3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}[,\.]\d{1,3})")
    for b in blocks:
        lines = [l for l in b.splitlines() if l.strip() != '']
        if not lines:
            continue
        # find time line
        time_line = None
        time_idx = None
        for i, ln in enumerate(lines):
            if '-->' in ln:
                time_line = ln
                time_idx = i
                break
        if not time_line:
            continue
        m = time_re.search(time_line)
        if not m:
            continue
        start_raw, end_raw = m.group(1), m.group(2)
        start = normalize_time(start_raw)
        end = normalize_time(end_raw)
        # text is lines after time line
        text_lines = lines[time_idx + 1 :]
        text = '\n'.join(text_lines).strip()
        cues.append((start, end, text))
    return cues


def build_vtt(cues: List[Tuple[str, str, str]], lang: str | None = None) -> str:
    out_lines = ['WEBVTT', '']
    if lang:
        out_lines.append(f'LANG: {lang}')
        out_lines.append('')
    for i, (start, end, text) in enumerate(cues, start=1):
        # index is optional in VTT; we omit numeric index to be minimal
        out_lines.append(f'{start} --> {end}')
        out_lines.extend(text.split('\n'))
        out_lines.append('')
    return '\n'.join(out_lines)


def detect_language_from_sample(text: str) -> str | None:
    try:
        from langdetect import detect
    except Exception:
        return None
    try:
        return detect(text)
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser(description='Convert SRT subtitle to VTT (WebVTT).')
    parser.add_argument('input', help='input .srt file')
    parser.add_argument('output', help='output .vtt file')
    parser.add_argument('--encoding', '-e', default=None, help='force input encoding (default: auto detect or utf-8)')
    parser.add_argument('--no-lang', action='store_true', help="don't attempt language detection or LANG header")
    args = parser.parse_args()

    enc = args.encoding or detect_encoding(args.input)
    try:
        with open(args.input, 'r', encoding=enc, errors='replace') as f:
            content = f.read()
    except Exception as ex:
        print(f'Error reading input file: {ex}', file=sys.stderr)
        sys.exit(2)

    cues = parse_srt(content)
    if not cues:
        print('No cues parsed from SRT. Is the file a valid SRT?', file=sys.stderr)
        sys.exit(3)

    lang = None
    if not args.no_lang:
        # sample first few cues for language detection
        sample = ' '.join([c[2] for c in cues[:5]])
        lang = detect_language_from_sample(sample)

    vtt_text = build_vtt(cues, lang)
    try:
        with open(args.output, 'w', encoding='utf-8') as out:
            out.write(vtt_text)
    except Exception as ex:
        print(f'Error writing output file: {ex}', file=sys.stderr)
        sys.exit(4)

    print(f'Converted {args.input} -> {args.output} (encoding: {enc}, lang: {lang})')


if __name__ == '__main__':
    main()
