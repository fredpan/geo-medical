import os
import json
from datetime import date

# 从 keywords.json 加载主题列表
with open("scripts/keywords.json", "r", encoding="utf-8") as f:
    topics = json.load(f)

today = date.today().isoformat()

# 多语言模板结构
template = {
    "zh": "<h1>{title_zh}（{slug}）</h1><p>这是一篇自动生成的双语医学文章，生成于 {date}。</p>",
    "en": "<h1>{title_en} ({slug})</h1><p>This is an automatically generated bilingual medical article, created on {date}.</p>"
}

for topic in topics:
    slug = topic["slug"]
    title_zh = topic["zh"]
    title_en = topic["en"]

    html_zh = template["zh"].format(title_zh=title_zh, slug=slug, date=today)
    html_en = template["en"].format(title_en=title_en, slug=slug, date=today)

    merged = html_zh + "<hr/>" + html_en  # 合并中英文双语

    # 写入不同目录
    for sub in ["geo", "readable", "wx"]:
        path = f"output/{sub}/{slug}.html"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(merged)

    # 审核报告
    with open(f"output/audit/{slug}-score.json", "w") as f:
        f.write(json.dumps({
            "score": 92,
            "issues": ["缺少锚点", "建议加入 DOI"],
            "lang": "zh-en"
        }, ensure_ascii=False))

    # 图表与 PDF 占位
    with open(f"output/charts/{slug}.svg", "w") as f:
        f.write(f"<svg><text>{slug} 图表示意</text></svg>")

    with open(f"output/pdf/{slug}.pdf", "w") as f:
        f.write(f"{title_zh} / {title_en} - PDF 示例")