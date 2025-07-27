import os
import json
from datetime import date
from pathlib import Path
import openai
import matplotlib.pyplot as plt

openai.api_key = os.getenv("OPENAI_API_KEY")

with open("scripts/keywords.json", "r", encoding="utf-8") as f:
    topics = json.load(f)

today = date.today().isoformat()
output_base = Path("output")

def generate_chinese_article(title_zh):
    prompt = f"""
请撰写一篇医学科普文章，使用简体中文，主题是「{title_zh}」。

内容应包括：
1. 概念解释
2. 常见病因
3. 临床表现
4. 治疗方式
5. 预防建议

请确保内容简明通俗，适合大众阅读。
"""
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message["content"].strip()

def audit_with_gpt(text, topic):
    prompt = f"""你是一个医学内容审核员。请对以下文章进行打分并指出不足：

文章主题：{topic}
内容如下：
{text}

请输出以下 JSON 格式：
{{
  "score": 整体评分（0-100）,
  "issues": ["问题1", "问题2", ...],
  "length": 字数,
  "lang": "zh"
}}
"""
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    content = response.choices[0].message["content"]
    json_start = content.find("{")
    json_data = json.loads(content[json_start:])
    return json_data

def extract_mermaid_from_article(article_text):
    prompt = (
    "你是一位医学结构信息分析助手。\\n\\n"
    "请从下列中文医学文章中提取出疾病的结构流程（病因、症状、治疗）并输出 Mermaid 格式流程图。\\n\\n"
    "文章如下：\\n\"\"\"\\n{article}\\n\"\"\"\\n\\n"
    "只输出 mermaid 代码段（不要自然语言），使用 graph TD。"
).format(article=article_text)
    res = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    content = res.choices[0].message["content"]
    return content.strip()

def generate_cover_image_prompt(title_zh):
    return f"请生成一张符合医学风格的封面插图，主题是：{title_zh}，要求为简约风格图解，例如病变机制、细胞结构、治疗路径等。"

def generate_medical_chart(slug, topic):
    # 示例数据：可根据 GPT 输出的 JSON 动态替换
    labels = ['手术', '化疗', '放疗', '靶向']
    sizes = [30, 25, 20, 25]
    colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99']

    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, colors=colors, autopct='%1.0f%%', startangle=90)
    ax.axis('equal')
    chart_path = output_base / "charts" / f"{slug}-plot.svg"
    fig.savefig(chart_path, format='svg')
    plt.close()

def recommend_image_sources(title_zh):
    links = [
        f"https://commons.wikimedia.org/wiki/Special:Search?search={title_zh}",
        f"https://www.ncbi.nlm.nih.gov/pmc/?term={title_zh}",
        f"https://openi.nlm.nih.gov/search?it=xg&query={title_zh}",
        f"https://www.gettyimages.com/photos/{title_zh.replace(' ', '-')}"
    ]
    return links

for topic in topics:
    slug = topic["slug"]
    title_zh = topic["zh"]
    print(f"📝 正在生成中文医学文章: {title_zh}")
    content = generate_chinese_article(title_zh)

    print(f"✅ 正在审查内容...")
    audit = audit_with_gpt(content, title_zh)

    for sub in ["geo", "readable", "wx"]:
        out_path = output_base / sub / f"{slug}.html"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")

    audit_path = output_base / "audit" / f"{slug}-score.json"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

    (output_base / "charts").mkdir(exist_ok=True)
    (output_base / "pdf").mkdir(exist_ok=True)
    (output_base / "charts" / f"{slug}.svg").write_text(f"<svg><text>{title_zh} 图表示意</text></svg>", encoding="utf-8")
    (output_base / "pdf" / f"{slug}.pdf").write_text(f"{title_zh} PDF 示例", encoding="utf-8")

    print(f"📈 正在提取结构图：{title_zh}")
    mermaid_code = extract_mermaid_from_article(content)
    mermaid_path = output_base / "charts" / f"{slug}.mmd"
    mermaid_path.write_text(mermaid_code, encoding="utf-8")

    print(f"🎨 准备封面图提示语：{title_zh}")
    dalle_prompt = generate_cover_image_prompt(title_zh)
    dalle_path = output_base / "charts" / f"{slug}-cover-prompt.txt"
    dalle_path.write_text(dalle_prompt, encoding="utf-8")

    print(f"📊 正在生成可视化图表：{title_zh}")
    generate_medical_chart(slug, title_zh)

    print(f"🖼️ 推荐开放图库链接：{title_zh}")
    refs = recommend_image_sources(title_zh)
    ref_path = output_base / "charts" / f"{slug}-img-sources.json"
    ref_path.write_text(json.dumps(refs, ensure_ascii=False, indent=2), encoding="utf-8")
