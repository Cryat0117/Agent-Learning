import csv, json

data = [{"name": "方源", "score": 95}, {"name": "方正", "score": 60}]
with open("students.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["name", "score"])
    writer.writeheader()
    writer.writerows(data)

with open("students.csv", "r", encoding="utf-8") as f:
    reader = list(csv.DictReader(f))
    avg = sum(float(r["score"]) for r in reader) / len(reader)

with open("result.json", "w", encoding="utf-8") as f:
    json.dump({"average": avg, "count": len(reader)}, f, indent=2, ensure_ascii=False)

print("处理完成！结果已存入 result.json")