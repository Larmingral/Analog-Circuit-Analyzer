import os
import glob
import re

def read_file_content(filepath):
    """读取文件原始文本内容"""
    if not filepath or not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"读取出错: {str(e)}"

def get_latest_html(directory, suffix):
    """智能寻找目录下后缀匹配的最新文件"""
    if not os.path.exists(directory):
        return None
    # 拼接查找模式，比如 ./html/*Laplace-Transfer.html
    pattern = os.path.join(directory, f"*{suffix}")
    files = glob.glob(pattern)
    if not files:
        return None
    # 按文件的最后修改时间寻找最新的一个
    latest_file = max(files, key=os.path.getmtime)
    return latest_file

def parse_slicap_to_markdown(html_content):
    """将 SLiCAP 导出的 HTML 转换为 Markdown"""
    if not html_content:
        return ""
    if html_content.startswith("读取出错"):
        return f"**{html_content}**"

    body_match = re.search(r'<body.*?>(.*?)</body>', html_content, re.DOTALL | re.IGNORECASE)
    text = body_match.group(1) if body_match else html_content
    text = re.sub(r'<div id="top">.*?</div>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<div id="footnote">.*?</div>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<!-- INSERT -->', '', text, flags=re.IGNORECASE)

    def replace_eq(match):
        return f"\n\n$$\n{match.group(1).strip()}\n$$\n\n"
    text = re.sub(r'\\begin\{equation\*?\}(.*?)\\end\{equation\*?\}', replace_eq, text, flags=re.DOTALL)

    def replace_eqnarray(match):
        return f"\n\n$$\n\\begin{{aligned}}\n{match.group(1).strip()}\n\\end{{aligned}}\n$$\n\n"
    text = re.sub(r'\\begin\{eqnarray\*?\}(.*?)\\end\{eqnarray\*?\}', replace_eqnarray, text, flags=re.DOTALL)

    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()