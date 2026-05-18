import os
import glob
import re
import fitz  # 【新增】这是 PyMuPDF 的包名


# ... (保留你之前的 read_file_content, clean_old_html, parse_slicap_to_markdown 等代码) ...

def convert_pdf_to_png(pdf_path):
    """【新增核心转换模块】：读取 PDF 并将其转换为高分辨率的 PNG 图片，返回图片路径"""
    if not pdf_path or not os.path.exists(pdf_path):
        return None
    try:
        # 生成同目录下的 .png 路径
        png_path = pdf_path.rsplit('.', 1)[0] + '.png'

        # 打开 PDF 文件
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)  # 波特图只有一页

        # 放大渲染分辨率（缩放系数 zoom=3 大约相当于 200+ DPI，非常清晰）
        zoom = 3.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        # 保存为 PNG
        pix.save(png_path)
        doc.close()

        return png_path
    except Exception as e:
        print(f"PDF 转 PNG 失败: {e}")
        return None

def read_file_content(filepath):
    """读取文件原始文本内容"""
    if not filepath or not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"读取出错: {str(e)}"

def clean_old_html(directory, suffix):
    """【新功能】：运行分析前，强制清理掉旧的 HTML 文件，防止报错时读取到过时数据"""
    if not os.path.exists(directory):
        return
    pattern = os.path.join(directory, f"*{suffix}")
    for f in glob.glob(pattern):
        try:
            os.remove(f)
        except Exception:
            pass

def get_latest_html(directory, suffix):
    """智能寻找目录下后缀匹配的最新文件"""
    if not os.path.exists(directory):
        return None
    pattern = os.path.join(directory, f"*{suffix}")
    files = glob.glob(pattern)
    if not files:
        return None
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

# ...保留你之前的代码，在末尾追加以下函数...

def get_svg_content(filepath):
    """读取 SVG 文件内容并直接作为 HTML 渲染"""
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            svg_data = f.read()
            # 剥离多余的 xml 声明，防止在网页中冲突
            svg_data = re.sub(r'<\?xml.*?\?>', '', svg_data, flags=re.IGNORECASE)
            return f"<div style='text-align: center;'>{svg_data}</div>"
    except Exception as e:
        return f"<p style='color:red;'>读取图像失败: {str(e)}</p>"