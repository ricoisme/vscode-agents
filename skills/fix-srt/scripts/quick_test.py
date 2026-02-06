#!/usr/bin/env python3
"""quick_test.py - 快速測試 fix_srt_enhanced.py 功能

用法：
  python quick_test.py
"""

import subprocess
import os

def run_test():
    """執行快速測試"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, 'fix_srt_enhanced.py')
    input_path = os.path.join(script_dir, 'test_input.srt')
    output_path = os.path.join(script_dir, 'test_output.srt')
    
    print("=" * 60)
    print("Fix SRT Enhanced - 快速功能測試")
    print("=" * 60)
    print()
    
    # 檢查檔案存在
    if not os.path.exists(script_path):
        print(f"❌ 找不到 fix_srt_enhanced.py")
        return
    
    if not os.path.exists(input_path):
        print(f"❌ 找不到測試檔案 test_input.srt")
        return
    
    print("📋 測試檔案：test_input.srt")
    print("📄 輸出檔案：test_output.srt")
    print()
    
    # 測試 1: 預覽模式
    print("🔍 測試 1: 預覽模式（--dry-run）")
    print("-" * 60)
    cmd1 = [
        'python', script_path,
        '--input', input_path,
        '--output', output_path,
        '--dry-run'
    ]
    subprocess.run(cmd1)
    print()
    
    # 測試 2: 實際執行（標準模式）
    print("⚙️  測試 2: 標準模式修正")
    print("-" * 60)
    cmd2 = [
        'python', script_path,
        '--input', input_path,
        '--output', output_path
    ]
    subprocess.run(cmd2)
    print()
    
    # 顯示結果
    if os.path.exists(output_path):
        print("✅ 修正完成！")
        print()
        print("📊 修正前後對比：")
        print("-" * 60)
        
        with open(input_path, 'r', encoding='utf-8') as f:
            original = f.read()
        
        with open(output_path, 'r', encoding='utf-8') as f:
            fixed = f.read()
        
        print("修正前範例（前 10 行）：")
        print(original.split('\n\n')[0:3])
        print()
        print("修正後範例（前 10 行）：")
        print(fixed.split('\n\n')[0:3])
        print()
        
        print(f"💾 完整輸出已儲存至: {output_path}")
        print()
        print("🎉 測試完成！請檢查輸出檔案以確認修正效果。")
    else:
        print("❌ 輸出檔案產生失敗")
    
    print()
    print("=" * 60)


if __name__ == '__main__':
    run_test()
