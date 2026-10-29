import csv
import json
from pathlib import Path
from typing import Any, List, Dict

def export_initial_student(file_path: Path) -> None:
    """
    写入初始学生数据到指定的CSV文件中。
    """
    data = [{"name": "方源", "score": 95}, {"name": "方正", "score": 60}]
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "score"])
        writer.writeheader()
        writer.writerows(data)

def analyze_student_scores(csv_path: Path, output_json_path: Path) -> Dict[str, Any]:
    """
    读取CSV、计算统计 指标并导出JSON报表,附带数据校验与容错防御
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"找不到指定文件：{csv_path}")

    valid_records: List[Dict[str, Any]] = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                score = float(row["score"])
                valid_records.append({"name": row["name"].strip(), "score": score})
            except (ValueError, KeyError) as e:
                print(f"【警告】跳过损坏数据{row}: {e}")
                continue

    if not valid_records:
        return {"average":0.0, "count":0, "status":"empty"}

    avg_score = sum(r["score"] for r in valid_records) / len(valid_records)
    summary = {
        "average": round(avg_score, 2),
        "count": len(valid_records),
        "data": valid_records
    }

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"分析完成！有效记录 {len(valid_records)} 条，平均分: {summary['average']}")
    return summary

if __name__ == "__main__":
    csv_file = Path("student.csv")
    json_file = Path("result.json")

    export_initial_student(csv_file)
    analyze_student_scores(csv_file, json_file)