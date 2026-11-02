import csv
import json
import math
from pathlib import Path

class DataAnalyzer:
    def __init__(self, csv_file: str, json_file: str):
        self.csv_file = Path(csv_file)
        self.json_file = Path(json_file)
        self.records = []
        self.skipped_reasons = {}

    def ensure_seed_data(self):
        """
        如果 CSV 不存在则自动写入种子数据，保障开箱即用
        """
        if self.csv_file.exists():
            return
        seed = [
            {"name": "方源", "score": 95},
            {"name": "方正", "score": 60},
            {"name": "白凝冰", "score": "缺考"}
        ]

        with open(self.csv_file, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "score"])
            writer.writeheader()
            writer.writerows(seed) 
        print(f"[创建] 已写入种子数据 {self.csv_file} ({len(seed)} 行)")

    def read_and_clean(self):
        """
        读取 CSV 并执行多维度防御清洗
        """
        try:
            with open(self.csv_file, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                fieldnames = set(reader.fieldnames or [])
                if not {"name", "score"}.issubset(fieldnames):
                        print(f"CSV 表头缺失。实际表头 = {fieldnames}，要求包含 {{'name', 'score'}}。")
                        return

                seen_names = set()

                for line_no, row in enumerate(reader, start=2):
                    raw_score = row.get("score")
                    name = (row.get("name") or "").strip()

                    try:
                        score = float(raw_score)
                    except (TypeError, ValueError):
                        self.skipped_reasons["非数字"] = self.skipped_reasons.get("非数字", 0) + 1
                        print(f"[跳过] 第 {line_no} 行：score={raw_score!r} 不是数字")
                        continue

                    if not math.isfinite(score):
                        self.skipped_reasons["NaN/Inf"] = self.skipped_reasons.get("NaN/Inf", 0) + 1
                        print(f"[跳过] 第 {line_no} 行：score={raw_score!r} 是 NaN 或 Inf")
                        continue

                    if not (0.0 <= score <= 100.0):
                        self.skipped_reasons["超出 0-100"] = self.skipped_reasons.get("超出 0-100", 0) + 1
                        print(f"[跳过] 第 {line_no} 行：score={score} 不在 [0.0, 100.0]")
                        continue

                    if not name:
                        self.skipped_reasons["姓名为空"] = self.skipped_reasons.get("姓名为空", 0) + 1
                        print(f"[跳过] 第 {line_no} 行：name={name!r} 为空")
                        continue

                    if name in seen_names:
                        self.skipped_reasons["重复姓名"] = self.skipped_reasons.get("重复姓名", 0) + 1
                        print(f"[跳过] 第 {line_no} 行：name={name!r} 重复")
                        continue

                    seen_names.add(name)
                    self.records.append({"name": name, "score": score})
        except FileNotFoundError:
            print(f"文件 {self.csv_file} 不存在，请检查路径。")
            return

        total_skipped = sum(self.skipped_reasons.values())
        print(f"[统计] 总共跳过 {total_skipped} 行，详情：{self.skipped_reasons}")

    def export_report(self):
        """
        计算平均分并导出与 W2 结构完全恒定的 JSON 报表
        """
        if not self.records:
            print("没有有效记录可导出。")
            return

        avg = sum(r["score"] for r in self.records) / len(self.records)
        summary = {
            "status": "success",
            "average": round(avg, 2),
            "count": len(self.records),
            "skipped": sum(self.skipped_reasons.values()),
            "skipped_reasons": self.skipped_reasons,
            "data": self.records,
        }

        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False, allow_nan=False)

        print(f"[导出] 已写入报告 {self.json_file}，平均分 {summary['average']}，有效记录 {summary['count']} 行")

if __name__ == "__main__":
    analyzer = DataAnalyzer("student.csv", "result.json")
    analyzer.ensure_seed_data()
    analyzer.read_and_clean()
    analyzer.export_report()