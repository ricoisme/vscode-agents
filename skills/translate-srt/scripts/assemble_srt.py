#!/usr/bin/env python3
"""
assemble_srt.py - 將翻譯後的 JSON chunks 組裝成兩個單語言 SRT 字幕檔

用法:
    python3 assemble_srt.py <TMPDIR> [INPUT_FILE] [SRC_LANG] [TGT_LANG]

參數:
    TMPDIR        臨時目錄路徑（包含 _translate_result_*.json）
    INPUT_FILE    原始影片路徑（用於決定輸出檔名）
                  若省略，輸出為 $TMPDIR/output.<lang>.srt
    SRC_LANG      來源語言代碼（預設 en）
    TGT_LANG      目標語言代碼（預設 zh）

輸出兩個檔案:
    <basename>.<tgt_lang>.srt  — 目標語言字幕
    <basename>.<src_lang>.srt  — 來源語言字幕
    （若 SRC_LANG == TGT_LANG，僅輸出一個 .<lang>.srt 檔）

範例:
    Ralph2.wav  en>zh  →  Ralph2.zh.srt + Ralph2.en.srt
    movie.mkv   ja>zh  →  movie.zh.srt  + movie.ja.srt
"""

import json
import glob
import os
import sys
import argparse


def load_results(tmpdir: str) -> list[dict]:
    """載入所有翻譯結果 JSON，依 index 排序後回傳。"""
    pattern = os.path.join(tmpdir, "_translate_result_*.json")
    chunk_files = sorted(glob.glob(pattern))

    if not chunk_files:
        print(f"錯誤：在 {tmpdir} 找不到任何翻譯結果檔案", file=sys.stderr)
        sys.exit(1)

    results = []
    for cf in chunk_files:
        with open(cf, "r", encoding="utf-8") as f:
            chunk = json.load(f)
        results.extend(chunk)

    results.sort(key=lambda x: x["index"])
    return results


def assemble_mono_srt(results: list[dict], field: str) -> str:
    """組裝單語言 SRT 字串，field 為 'tgt' 或 'src'。"""
    lines = []
    for entry in results:
        lines.append(str(entry["index"]))
        lines.append(entry["timecode"])
        lines.append(entry[field])
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="將翻譯後的 JSON chunks 組裝成兩個單語言 SRT"
    )
    parser.add_argument("tmpdir", help="臨時目錄路徑")
    parser.add_argument(
        "input_file",
        nargs="?",
        default="",
        help="原始影片路徑（用於決定輸出檔名）",
    )
    parser.add_argument(
        "src_lang",
        nargs="?",
        default="en",
        help="來源語言代碼（預設 en）",
    )
    parser.add_argument(
        "tgt_lang",
        nargs="?",
        default="zh",
        help="目標語言代碼（預設 zh）",
    )
    args = parser.parse_args()

    results = load_results(args.tmpdir)

    if args.input_file:
        base = os.path.splitext(args.input_file)[0]
    else:
        base = os.path.join(args.tmpdir, "output")

    tgt_path = f"{base}.{args.tgt_lang}.srt"
    tgt_content = assemble_mono_srt(results, "tgt")
    with open(tgt_path, "w", encoding="utf-8") as f:
        f.write(tgt_content)
    print(f"目標語言字幕已輸出至: {tgt_path}")

    if args.src_lang != args.tgt_lang:
        src_path = f"{base}.{args.src_lang}.srt"
        src_content = assemble_mono_srt(results, "src")
        with open(src_path, "w", encoding="utf-8") as f:
            f.write(src_content)
        print(f"來源語言字幕已輸出至: {src_path}")

    print(f"共 {len(results)} 條字幕")


if __name__ == "__main__":
    main()
