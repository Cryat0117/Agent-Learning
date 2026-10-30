import csv
import json
import math
from pathlib import Path
from typing import Any, List, Dict

SCORE_MIN, SCORE_MAX = 0.0, 100.0

def ensure_seed_data(csv_path: Path) -> None:
    """
    仅当 csv 不存在时，写入一份种子数据。已存在则原样保留。
    """
    if csv_path.exists():
        print(f"[跳过] {csv_path} 已存在，不覆盖(保留你手工造的数据)")
        return
    seed = [
        {"name": "方源", "score": 95}, 
        {"name": "方正", "score": 60},
        {"name": "白凝冰", "score": "缺考"}
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "score"])
        writer.writeheader()
        writer.writerows(seed)
    print(f"[创建] 已写入种子数据 {csv_path} ({len(seed)} 行)")

def analyze_student_scores(csv_path: Path, output_json_path: Path) -> Dict[str, Any]:
    """
    读取CSV、计算统计 指标并导出JSON报表,附带数据校验与容错防御
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"找不到指定文件：{csv_path}")

    valid_records: List[Dict[str, Any]] = []
    seen_names: set[str] = set()
    skipped_reasons: Dict[str, int] = {}

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        required = {"name", "score"}
        if not required.issubset(set(fieldnames)):
            raise ValueError(
                f"CSV 表头缺失。实际表头 = {fieldnames}，要求包含 {required}。"
                f"(常见原因：文件编码不是 UTF-8,或列名被改过)"
            )
        for line_no, row in enumerate(reader, start=2):
            raw_score = row.get("score")
            name = (row.get("name") or "").strip()
            try:
                score = float(raw_score) # type: ignore[arg-type]
            except (TypeError, ValueError):    
                skipped_reasons["非数字"] = skipped_reasons.get("非数字", 0) + 1
                print(f"[跳过] 第 {line_no} 行：score={raw_score!r} 不是数字")
                continue

            if not math.isfinite(score):
                skipped_reasons["NaN/Inf"] = skipped_reasons.get("NaN/Inf", 0) + 1
                print(f"[跳过] 第 {line_no} 行：score={raw_score!r} 是 NaN 或 Inf")
                continue

            if not(SCORE_MIN <= score <= SCORE_MAX):
                skipped_reasons["超出 0-100"] = skipped_reasons.get("超出 0-100", 0) + 1
                print(f"[跳过] 第 {line_no} 行：score={score} 不在 [{SCORE_MIN}, {SCORE_MAX}]")
                continue

            if not name:
                skipped_reasons["姓名为空"] = skipped_reasons.get("姓名为空", 0) + 1
                print(f"[跳过] 第 {line_no} 行：姓名为空")
                continue

            if name in seen_names:
                skipped_reasons["重复姓名"] = skipped_reasons.get("重复姓名", 0) + 1
                print(f"[跳过] 第 {line_no} 行：{name} 重复（已有记录）")
                continue

            seen_names.add(name)
            valid_records.append({"name": name, "score": score})

    skipped_total = sum(skipped_reasons.values())

    if not valid_records:
         raise ValueError(
            f"没有任何一条有效记录（共跳过 {skipped_total} 条：{skipped_reasons}）。"
            f"全部失败通常意味着表头或编码有问题，请先检查文件本身。"
        )
    avg_score = sum(r["score"] for r in valid_records) / len(valid_records)
    summary: Dict[str, Any] = {
        "status": "ok",
        "average": round(avg_score, 2),
        "count": len(valid_records),
        "skipped": skipped_total,
        "skipped_reasons": skipped_reasons,
        "data": valid_records,
    }

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(
        f"\n[完成] 有效 {len(valid_records)} 条，跳过 {skipped_total} 条，"
        f"平均分 {summary['average']} → 已写入 {output_json_path}"
    )
    return summary

if __name__ == "__main__":
    csv_file = Path("student.csv")
    json_file = Path("result.json")

    ensure_seed_data(csv_file)
    analyze_student_scores(csv_file, json_file)