#!/usr/bin/env python3
"""
verify_translation.py - 驗證翻譯結果品質，偵測禁用字元等常見錯誤

用法:
    python3 verify_translation.py <TMPDIR> <TGT_LANG>

參數:
    TMPDIR      臨時目錄路徑（包含 _translate_result_*.json）
    TGT_LANG    目標語言代碼（例如 zh、en、ja）

目前驗證規則:
    zh：偵測音譯人名中禁用的「乘」（U+4E58）字

結束碼:
    0  驗證通過
    1  發現錯誤（輸出錯誤清單）
    2  引數或檔案錯誤
"""

import json
import glob
import os
import sys
import argparse

# 各語言的禁用字元定義 {lang_code: {char: description}}
FORBIDDEN_CHARS: dict[str, dict[str, str]] = {
    "zh": {
        chr(0x4E58): "U+4E58「乘」（禁用於音譯人名/地名）",
    },
}


def verify(tmpdir: str, tgt_lang: str) -> list[str]:
    """驗證翻譯結果，回傳錯誤訊息清單。"""
    pattern = os.path.join(tmpdir, "_translate_result_*.json")
    chunk_files = sorted(glob.glob(pattern))

    if not chunk_files:
        print(f"警告：在 {tmpdir} 找不到翻譯結果檔案", file=sys.stderr)
        return []

    bad_chars = FORBIDDEN_CHARS.get(tgt_lang, {})
    errors: list[str] = []
    total_entries = 0

    for cf in chunk_files:
        with open(cf, "r", encoding="utf-8") as f:
            chunk = json.load(f)
        total_entries += len(chunk)
        for entry in chunk:
            tgt = entry.get("tgt", "")
            for char, desc in bad_chars.items():
                if char in tgt:
                    errors.append(
                        f"Index {entry['index']}: 包含禁用字元 {desc} → {tgt}"
                    )

    print(f"驗證完成：共 {total_entries} 條、{len(chunk_files)} 個批次檔案")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(
        description="驗證翻譯結果品質，偵測禁用字元等常見錯誤"
    )
    parser.add_argument("tmpdir", help="臨時目錄路徑")
    parser.add_argument("tgt_lang", help="目標語言代碼（如 zh、en、ja）")
    args = parser.parse_args()

    if not os.path.isdir(args.tmpdir):
        print(f"錯誤：目錄不存在：{args.tmpdir}", file=sys.stderr)
        sys.exit(2)

    errors = verify(args.tmpdir, args.tgt_lang)

    if errors:
        print(f"\n發現 {len(errors)} 個錯誤：")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("✓ 驗證通過，未發現錯誤")
        sys.exit(0)


if __name__ == "__main__":
    main()
