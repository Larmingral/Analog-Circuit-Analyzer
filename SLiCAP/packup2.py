import gradio as gr
import os
import subprocess
import matplotlib.pyplot as plt
import re
from dashscope import Generation

# 要运行的脚本文件名
aaa = "demo.py"


def read_file_content(filepath):
    """读取文件原始文本内容"""
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"读取出错: {str(e)}"


def parse_slicap_to_markdown(html_content):
    """
    【全新核心逻辑】：将 SLiCAP 导出的 HTML 智能解析转换为 Gradio 原生支持的 Markdown + KaTeX 公式。
    不仅完美解决公式无法渲染的问题，同时彻底弃用了 iframe，完全融入网页瀑布流中。
    """
    if not html_content:
        return "*未找到生成的 HTML 文件，请检查分析脚本是否成功运行。*"
    if html_content.startswith("读取出错"):
        return f"**{html_content}**"

    # 1. 提取 <body> 内部的内容
    body_match = re.search(r'<body.*?>(.*?)</body>', html_content, re.DOTALL | re.IGNORECASE)
    text = body_match.group(1) if body_match else html_content

    # 2. 剥离掉原 HTML 多余的排版头尾（标题和底部版权信息），保持页面干净
    text = re.sub(r'<div id="top">.*?</div>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<div id="footnote">.*?</div>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<!-- INSERT -->', '', text, flags=re.IGNORECASE)

    # 3. 将 \begin{equation}...\end{equation} 转换为 Gradio/Markdown 完美支持的 $$...$$ 显示公式格式
    def replace_eq(match):
        eq_core = match.group(1).strip()
        return f"\n\n$$\n{eq_core}\n$$\n\n"

    text = re.sub(r'\\begin\{equation\*?\}(.*?)\\end\{equation\*?\}', replace_eq, text, flags=re.DOTALL)

    # 4. 万一出现 \begin{eqnarray}，将其转换为兼容性更好的 aligned 格式
    def replace_eqnarray(match):
        eq_core = match.group(1).strip()
        return f"\n\n$$\n\\begin{{aligned}}\n{eq_core}\n\\end{{aligned}}\n$$\n\n"

    text = re.sub(r'\\begin\{eqnarray\*?\}(.*?)\\end\{eqnarray\*?\}', replace_eqnarray, text, flags=re.DOTALL)

    # 清除多余的空行并返回
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def run_my_analysis():
    """核心分析函数：运行脚本 + 读取HTML提取公式 + 调用大模型 + 生成图表"""
    file_content = ""

    # 1. 运行外部Python脚本
    result = subprocess.run(
        f"python {aaa}",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="ignore"
    )

    # 2. 读取电路网表文件
    try:
        with open("./cir/circuit.cir", "r", encoding="utf-8") as f:
            file_content = f.read()
    except FileNotFoundError:
        file_content = "【错误】：未找到网表文件 ./cir/circuit.cir"
    except Exception as e:
        file_content = f"【错误】：读取网表失败：{str(e)}"

    # 3. 读取生成的两个 HTML 分析结果，并直接转化为纯净的 Markdown 公式
    raw_laplace = read_file_content("./html/Vcc_Laplace-Transfer.html")
    raw_matrix = read_file_content("./html/Vcc_Matrix-Equations.html")

    md_laplace = parse_slicap_to_markdown(raw_laplace)
    md_matrix = parse_slicap_to_markdown(raw_matrix)

    # 4. 构建给大模型的数据上下文 (喂干净的公式文本给模型，理解效果更好)
    llm_context = ""
    if md_laplace and "未找到" not in md_laplace:
        llm_context += f"--- 传递函数 (Laplace Transfer) ---\n{md_laplace}\n\n"
    if md_matrix and "未找到" not in md_matrix:
        llm_context += f"--- 矩阵方程 (Matrix Equations) ---\n{md_matrix}\n\n"

    if result.stderr:
        llm_context += f"--- 脚本错误日志参考 ---\n{result.stderr}\n\n"

    # 5. 调用通义千问大模型分析结果
    llm_analysis_result = ""
    if file_content and llm_context.strip() and "未找到网表文件" not in file_content:
        messages = [
            {'role': 'system',
             'content': (
                 "你是一位顶级的电子电路分析专家。我将为你提供电路的网表文件（Netlist）以及通过 SLiCAP 提取的电路公式（传递函数和矩阵方程）。\n"
                 "为了保证分析报告的严谨性和专业度，请你**务必严格按照以下四个模块的顺序和格式**进行输出：\n\n"
                 "### 一、 电路拓扑与基础分析\n"
                 "基于提供的原电路网表，分析这是一个什么类型的电路。**必须使用一个 Markdown 表格**来总结电路中的关键节点（Nodes）、核心元器件（Components）及其物理作用。\n\n"
                 "### 二、 拉普拉斯传递函数 (Laplace Transfer)\n"
                 "1. **公式渲染**：首先，将传递函数使用块级公式 `$$ ... $$` 准确无误地渲染出来，方便对照。\n"
                 "2. **特性剖析**：结合网表中的器件参数详细分析增益特性、零极点分布及核心物理意义。\n\n"
                 "### 三、 节点电压矩阵方程 (Matrix Equations)\n"
                 "1. **矩阵渲染**：首先，将矩阵方程使用块级公式 `$$ ... $$` 准确无误地渲染出来。\n"
                 "2. **方程解析**：解释矩阵维度含义，说明对角线与非对角线元素对应的物理联系。\n\n"
                 "### 四、 综合性能评估\n"
                 "一到两句话总结该电路的整体性能表现、潜在的应用场景或优缺点。\n\n"
                 "⚠️ 【极度重要的排版规范】：\n"
                 "为了防止 Markdown 解析引擎冲突，正文中的**所有行内变量、带下标的符号**（例如跨导 \\(g_m\\)、电阻 \\(R_l\\)、基极电阻 \\(r_\\pi\\) 等），**绝对禁止使用单美元符号 `$ ... $` 包裹**，请**务必全部使用 `\\( ... \\)` 来包裹**！\n"
                 "（正确示例：通过调节 \\(g_m\\) 和 \\(R_l\\) 的阻值...；错误示例：通过调节 $g_m$ 和 $R_l$ 的阻值...）"
             )},
            {'role': 'user',
             'content': (
                 f"请根据上述要求的格式，为以下电路生成专业的分析报告。\n\n"
                 f"【提取的公式内容】（请在第二、三部分准确渲染它们）：\n{llm_context}\n\n"
                 f"【原电路网表内容】：\n{file_content}"
             )}
        ]

        try:
            response = Generation.call(
                api_key=os.environ.get("DASHSCOPE_API_KEY"),
                model="qwen-plus",
                messages=messages,
                result_format="message"
            )
            if response.status_code == 200:
                llm_analysis_result = response.output.choices[0].message.content
            else:
                llm_analysis_result = f"大模型调用失败：{response.message}"
        except Exception as e:
            llm_analysis_result = f"大模型调用异常：{str(e)}"
    else:
        llm_analysis_result = "无法调用大模型：生成的分析文件缺失或电路网表读取失败。"

    # 6. 生成图表
    fig = plt.figure(figsize=(8, 4))
    plt.text(0.5, 0.5, "分析数据图表（后续可替换）", ha="center", fontsize=12)
    plt.axis("off")
    plt.close(fig)

    return md_laplace, md_matrix, file_content, llm_analysis_result, fig


# 构建Gradio界面
with gr.Blocks(theme=gr.themes.Soft(), title="我的分析工具") as demo:
    gr.Markdown("### 📝 一键电路分析工具")

    btn = gr.Button("开始分析", variant="primary", size="lg")

    # 全局瀑布流排版：去掉了任何 iframe 或者固定高度的组件
    gr.Markdown("#### 📜 原电路网表内容")
    circuit_text = gr.Textbox(
        lines=10,
        show_label=False,
        placeholder="网表内容会在这里展示~",
        interactive=False
    )

    gr.Markdown("#### 📐 Laplace Transfer (拉普拉斯传递函数)")
    # 【改动】：从原先的 gr.HTML 变为了自带强大渲染能力的 gr.Markdown 组件
    out_laplace = gr.Markdown()

    gr.Markdown("#### 🧮 Matrix Equations (矩阵方程)")
    # 【改动】：同上
    out_matrix = gr.Markdown()

    gr.Markdown("#### 🤖 大模型深度分析结果")
    res_markdown = gr.Markdown(
        value="大模型根据公式推导的分析结果会显示在这里~",
        latex_delimiters=[
            {"left": "$$", "right": "$$", "display": True},
            {"left": r"\(", "right": r"\)", "display": False},
            {"left": "$", "right": "$", "display": False}
        ]
    )

    gr.Markdown("#### 📊 结果图表")
    res_fig = gr.Plot()

    # 绑定组件
    btn.click(
        fn=run_my_analysis,
        outputs=[out_laplace, out_matrix, circuit_text, res_markdown, res_fig]
    )

if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        max_threads=1
    )