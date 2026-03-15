#!/usr/bin/env python3
"""
parse_srt.py - 解析 SRT 字幕檔並分批輸出 JSON chunks

用法:
    python3 parse_srt.py <TMPDIR> [--batch-size N]

參數:
    TMPDIR        臨時目錄路徑（包含 _translate_temp_src.srt）
    --batch-size  每批字幕條數（預設 40）

輸出:
    $TMPDIR/_translate_chunk_0.json
    $TMPDIR/_translate_chunk_1.json
    ...（每個 chunk 包含最多 batch-size 條字幕）

輸出格式（每個 JSON 陣列元素）:
    {"index": 1, "timecode": "00:00:09,490 --> 00:00:11,992", "text": "原文字幕"}
"""

import re
import json
import sys
import os
import argparse


def parse_srt(filepath: str) -> list[dict]:
    """解析 SRT 檔案，回傳字幕條目清單。"""
    with open(filepath, "r", encoding="utf-8-sig") as f:
        content = f.read()

    blocks = re.split(r"\n\s*\n", content.strip())
    entries = []

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue

        try:
            idx = int(lines[0].strip())
        except ValueError:
            continue

        timecode = lines[1].strip()
        text = " ".join(line.strip() for line in lines[2:])

        entries.append({
            "index": idx,
            "timecode": timecode,
            "text": text,
        })

    return entries


def main() -> None:
    parser = argparse.ArgumentParser(
        description="解析 SRT 字幕檔並分批輸出 JSON chunks"
    )
    parser.add_argument("tmpdir", help="臨時目錄路徑")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=40,
        metavar="N",
        help="每批字幕條數（預設 40）",
    )
    args = parser.parse_args()

    srt_path = os.path.join(args.tmpdir, "_translate_temp_src.srt")

    if not os.path.isfile(srt_path):
        print(f"錯誤：找不到 SRT 檔案：{srt_path}", file=sys.stderr)
        sys.exit(1)

    entries = parse_srt(srt_path)

    if not entries:
        print("錯誤：SRT 檔案中未解析到任何字幕條目", file=sys.stderr)
        sys.exit(1)

    batch_size = args.batch_size
    chunks = [
        entries[i : i + batch_size] for i in range(0, len(entries), batch_size)
    ]

    for ci, chunk in enumerate(chunks):
        outpath = os.path.join(args.tmpdir, f"_translate_chunk_{ci}.json")
        with open(outpath, "w", encoding="utf-8") as f:
            json.dump(chunk, f, ensure_ascii=False, indent=2)

    summary = {"total_entries": len(entries), "total_chunks": len(chunks)}
    print(f"總共 {len(entries)} 條字幕，分成 {len(chunks)} 批")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
