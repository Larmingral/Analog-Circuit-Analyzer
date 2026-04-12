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
    """
    if not html_content:
        return "*未找到生成的 HTML 文件，请检查分析脚本是否成功运行。*"
    if html_content.startswith("读取出错"):
        return f"**{html_content}**"

    body_match = re.search(r'<body.*?>(.*?)</body>', html_content, re.DOTALL | re.IGNORECASE)
    text = body_match.group(1) if body_match else html_content
    text = re.sub(r'<div id="top">.*?</div>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<div id="footnote">.*?</div>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<!-- INSERT -->', '', text, flags=re.IGNORECASE)

    def replace_eq(match):
        eq_core = match.group(1).strip()
        return f"\n\n$$\n{eq_core}\n$$\n\n"

    text = re.sub(r'\\begin\{equation\*?\}(.*?)\\end\{equation\*?\}', replace_eq, text, flags=re.DOTALL)

    def replace_eqnarray(match):
        eq_core = match.group(1).strip()
        return f"\n\n$$\n\\begin{{aligned}}\n{eq_core}\n\\end{{aligned}}\n$$\n\n"

    text = re.sub(r'\\begin\{eqnarray\*?\}(.*?)\\end\{eqnarray\*?\}', replace_eqnarray, text, flags=re.DOTALL)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def mock_image_to_netlist(image_path):
    """
    【预留的图片转网表函数】：
    目前功能没做完，所以这只是个占位符。
    未来这里将接入你的图像识别算法。当前为了跑通流程，它会尝试读取本地默认网表返回。
    """
    if not image_path:
        return "请先上传或拍摄图片！"

    # 临时逻辑：尝试读取现有的 circuit.cir，如果读不到则给一个示例模板
    try:
        with open("./cir/circuit.cir", "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return "*这是一个占位符*\n*未来这里会显示识别出来的网表*\nV1 1 0 5V\nR1 1 2 1k\n..."


def run_my_analysis(ui_netlist_text):
    """
    核心分析函数：接收前端右侧文本框里的网表 -> 写入文件 -> 运行脚本 -> 读取公式 -> 调用大模型 -> 生成图表
    """
    if not ui_netlist_text or ui_netlist_text.strip() == "":
        return "错误：网表内容为空", "错误：网表内容为空", "大模型分析失败：未提供网表。", None

    # 【新加逻辑】：把前端传过来的/编辑后的网表，先写回到 ./cir/circuit.cir 文件中，
    # 这样后续外部的 demo.py 才能读取到最新的网表进行分析。
    os.makedirs("./cir", exist_ok=True)
    try:
        with open("./cir/circuit.cir", "w", encoding="utf-8") as f:
            f.write(ui_netlist_text)
    except Exception as e:
        return f"写入网表出错", f"写入网表出错", f"保存网表文件失败: {str(e)}", None

    # 1. 运行外部Python脚本
    result = subprocess.run(
        f"python {aaa}",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="ignore"
    )

    # 2. 读取生成的两个 HTML 分析结果，并直接转化为纯净的 Markdown 公式
    raw_laplace = read_file_content("./html/Vdd_Laplace-Transfer.html")
    raw_matrix = read_file_content("./html/Vdd_Matrix-Equations.html")

    md_laplace = parse_slicap_to_markdown(raw_laplace)
    md_matrix = parse_slicap_to_markdown(raw_matrix)

    # 3. 构建给大模型的数据上下文
    llm_context = ""
    if md_laplace and "未找到" not in md_laplace:
        llm_context += f"--- 传递函数 (Laplace Transfer) ---\n{md_laplace}\n\n"
    if md_matrix and "未找到" not in md_matrix:
        llm_context += f"--- 矩阵方程 (Matrix Equations) ---\n{md_matrix}\n\n"

    if result.stderr:
        llm_context += f"--- 脚本错误日志参考 ---\n{result.stderr}\n\n"

    # 4. 调用大模型
    llm_analysis_result = ""
    if ui_netlist_text and llm_context.strip():
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
                 f"【原电路网表内容】：\n{ui_netlist_text}"
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
        llm_analysis_result = "无法调用大模型：生成的分析文件缺失或网表为空。"

    # 5. 生成图表
    fig = plt.figure(figsize=(8, 4))
    plt.text(0.5, 0.5, "分析数据图表（后续可替换）", ha="center", fontsize=12)
    plt.axis("off")
    plt.close(fig)

    return md_laplace, md_matrix, llm_analysis_result, fig


# 构建Gradio界面
with gr.Blocks(theme=gr.themes.Soft(), title="智能电路识别与分析系统") as demo:
    gr.Markdown("### 📝 智能电路图识别与一键分析工具")

    # ================= 核心改造区域：图像输入与网表预留区 =================
    with gr.Row():
        # 左栏：图像输入区
        with gr.Column(scale=1):
            gr.Markdown("#### 📷 1. 拍摄或上传电路图")
            # sources=["upload", "webcam", "clipboard"] 让这个组件同时支持：文件上传、摄像头拍照、剪贴板粘贴
            img_input = gr.Image(
                sources=["upload", "webcam", "clipboard"],
                type="filepath",
                label="上传电路图片"
            )
            # 预留的转换按钮
            btn_img_to_netlist = gr.Button("⚡ 识别提取网表", variant="secondary")

        # 右栏：网表文本区
        with gr.Column(scale=1):
            gr.Markdown("#### 📜 2. 电路网表内容 (可手动编写)")
            circuit_text = gr.Textbox(
                lines=12,
                show_label=False,
                placeholder="网表内容将在这里生成，你也可以直接在这里手动编写或修改~",
                interactive=True  # 设置为True，允许用户手动修改网表内容
            )
            # 点击后才对右侧的内容进行深度分析
            btn_analyze = gr.Button("🚀 3. 根据网表开始分析", variant="primary")

    gr.Markdown("---")

    # ================= 瀑布流结果展示区 =================
    gr.Markdown("#### 📐 Laplace Transfer (拉普拉斯传递函数)")
    out_laplace = gr.Markdown()

    gr.Markdown("#### 🧮 Matrix Equations (矩阵方程)")
    out_matrix = gr.Markdown()

    gr.Markdown("#### 🤖 大模型深度分析结果")
    res_markdown = gr.Markdown(
        value="等待分析...",
        latex_delimiters=[
            {"left": "$$", "right": "$$", "display": True},
            {"left": r"\(", "right": r"\)", "display": False},
            {"left": "$", "right": "$", "display": False}
        ]
    )

    gr.Markdown("#### 📊 结果图表")
    res_fig = gr.Plot()

    # ================= 事件绑定 =================

    # 动作 1：图片转网表（绑定占位函数）
    btn_img_to_netlist.click(
        fn=mock_image_to_netlist,
        inputs=[img_input],
        outputs=[circuit_text]
    )

    # 动作 2：网表分析核心流程
    # 注意：这里的 inputs 改为了 circuit_text，意味着分析函数使用的是当前文本框里的网表数据
    btn_analyze.click(
        fn=run_my_analysis,
        inputs=[circuit_text],
        outputs=[out_laplace, out_matrix, res_markdown, res_fig]
    )

if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        max_threads=1
    )