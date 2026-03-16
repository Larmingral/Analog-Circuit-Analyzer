import gradio as gr
import os
import subprocess
import matplotlib.pyplot as plt
import html
from dashscope import Generation

# 要运行的脚本文件名
aaa = "demo.py"


def read_file_content(filepath):
    """
    读取文件原始文本内容，用于后续喂给大模型。
    """
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"读取出错: {str(e)}"


def create_iframe(content, height="350px"):
    """
    将读取到的HTML文本内容封装为iframe格式以供前端安全展示。
    """
    if content is None:
        return "<div style='color:red; padding:20px; border:1px solid red;'>未找到生成的 HTML 文件，请检查分析脚本是否成功运行。</div>"
    if content.startswith("读取出错"):
        return f"<div style='color:red; padding:20px;'>{content}</div>"

    # 对HTML内容进行转义，以安全地放入srcdoc属性中
    escaped_content = html.escape(content)
    return f'<iframe srcdoc="{escaped_content}" style="width:100%; height:{height}; border:none;"></iframe>'


def run_my_analysis():
    """核心分析函数：运行脚本 + 读取HTML作为上下文 + 调用大模型 + 生成图表"""
    file_content = ""

    # 1. 运行外部Python脚本
    # (此时忽略正常输出，但捕获错误输出以便排查运行失败的情况)
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

    # 3. 读取生成的两个 HTML 分析结果文件的原始内容
    # （如果您的 HTML 存在其他文件夹，如 html/Vcc_Laplace-Transfer.html，请在这里更改路径）
    raw_laplace = read_file_content("./html/Vcc_Laplace-Transfer.html")
    raw_matrix = read_file_content("./html/Vcc_Matrix-Equations.html")

    # 转换为前端展示用的 iframe
    html_laplace = create_iframe(raw_laplace, height="250px")
    html_matrix = create_iframe(raw_matrix, height="400px")

    # 4. 构建给大模型的数据上下文
    llm_context = ""
    if raw_laplace:
        llm_context += f"--- 传递函数 (Laplace Transfer) ---\n{raw_laplace}\n\n"
    if raw_matrix:
        llm_context += f"--- 矩阵方程 (Matrix Equations) ---\n{raw_matrix}\n\n"

    if result.stderr:
        llm_context += f"--- 脚本错误日志参考 ---\n{result.stderr}\n\n"

    # 5. 调用通义千问大模型分析结果
    llm_analysis_result = ""
    if file_content and llm_context.strip() and "未找到网表文件" not in file_content:
        # 修改了系统提示词，告诉模型从含有LaTeX公式的HTML中读取数据
        messages = [
            {'role': 'system',
             'content': '你是一个专业的电路分析助手。我将为你提供电路的网表文件，以及通过SLiCAP生成的分析结果(以包含LaTeX数学公式的HTML源码形式提供)。请你从中提取电路的节点电压矩阵方程和拉普拉斯传递函数，并结合网表对电路的性能、增益特性等进行简要的概述和物理分析，语言务必专业且简洁明了。'},
            {'role': 'user',
             'content': f'以下是分析结果文件的内容：\n{llm_context}\n\n对应的原电路网表内容是：\n{file_content}'}
        ]

        try:
            response = Generation.call(
                api_key="sk-0a85c32631604fb496aa4a4152f323e5",  # 请替换为真实的API_KEY
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
    fig = plt.figure(figsize=(6, 3))
    plt.text(0.5, 0.5, "分析数据图表（后续可替换）", ha="center", fontsize=12)
    plt.axis("off")
    plt.close(fig)

    return html_laplace, html_matrix, file_content, llm_analysis_result, fig


# 构建Gradio界面
with gr.Blocks(theme=gr.themes.Soft(), title="我的分析工具") as demo:
    gr.Markdown("### 📝 一键电路分析工具")

    with gr.Row():
        # 左栏：展示HTML分析结果
        with gr.Column():
            gr.Markdown("#### 📐 Laplace Transfer (拉普拉斯传递函数)")
            html_out1 = gr.HTML(label="Laplace Transfer")

            gr.Markdown("#### 🧮 Matrix Equations (矩阵方程)")
            html_out2 = gr.HTML(label="Matrix Equations")

        # 右栏：原网表内容
        with gr.Column():
            circuit_text = gr.Textbox(
                label="原电路网表内容",
                lines=22,
                placeholder="网表内容会在这里展示~",
                interactive=False
            )

    res_text2 = gr.Textbox(label="大模型深度分析结果", lines=8, placeholder="大模型根据公式推导的分析结果会显示在这里~")
    res_fig = gr.Plot(label="结果图表")

    # 分析按钮
    btn = gr.Button("开始分析", variant="primary", size="lg")

    # 绑定组件
    btn.click(
        fn=run_my_analysis,
        outputs=[html_out1, html_out2, circuit_text, res_text2, res_fig]
    )


if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        max_threads=1
    )