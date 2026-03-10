import gradio as gr
import os
import subprocess
import matplotlib.pyplot as plt
from dashscope import Generation

# 要运行的脚本文件名
aaa = "test_slicap.py"
# 全局变量存储大模型分析结果
llm_analysis_result = ""

def run_my_analysis():
    """核心分析函数：运行脚本 + 调用大模型 + 生成图表 + 返回网表内容"""
    global llm_analysis_result
    llm_analysis_result = ""  # 每次运行先清空
    file_content = ""  # 局部变量存储网表内容（关键修复）

    # 1. 运行外部Python脚本，捕获输出和错误
    result = subprocess.run(
        f"python {aaa}",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="ignore"
    )

    # 整理脚本运行结果
    analysis_result = result.stdout
    if result.stderr:
        analysis_result += f"\n\n【程序运行提示】：{result.stderr}"

    # 2. 读取电路网表文件
    try:
        with open("./cir/my_circuit.cir", "r", encoding="utf-8") as f:
            file_content = f.read()  # 赋值给局部变量，而非全局
    except FileNotFoundError:
        analysis_result += "\n\n【警告】：未找到电路网表文件 ./cir/my_circuit.cir，请检查路径！"
        file_content = "【错误】：未找到网表文件 ./cir/my_circuit.cir"
    except Exception as e:
        analysis_result += f"\n\n【文件读取错误】：{str(e)}"
        file_content = f"【错误】：读取网表失败：{str(e)}"

    # 3. 调用通义千问大模型分析结果
    if file_content and analysis_result.strip() and "未找到网表文件" not in file_content:
        messages = [
            {'role': 'system',
             'content': '你是一个电路分析的助手，请根据网表和生成的分析结果，对电路性能进行一个简要的分析和概述，语言简洁明了。'},
            {'role': 'user', 'content': f'请分析以下电路分析结果：{analysis_result}\n\n对应的电路网表是：{file_content}'}
        ]

        try:
            response = Generation.call(
                api_key="sk-0a85c32631604fb496aa4a4152f323e5",
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
        llm_analysis_result = "无法调用大模型：脚本运行结果或电路网表为空"

    # 4. 生成图表（修复阻塞问题）
    fig = plt.figure(figsize=(6, 3))
    plt.text(0.5, 0.5, "分析数据图表（后续可替换）", ha="center", fontsize=12)
    plt.axis("off")
    plt.close(fig)

    # 关键修复：返回值增加file_content，对应右侧网表栏
    return analysis_result, file_content, llm_analysis_result, fig

# 构建Gradio界面
with gr.Blocks(theme=gr.themes.Soft(), title="我的分析工具") as demo:
    gr.Markdown("### 📝 一键电路分析工具")

    with gr.Row():
        # 左栏：分析结果
        with gr.Column():
            res_text1 = gr.Textbox(
                label="分析结果（终端输出）",
                lines=12,
                placeholder="点击分析，结果会显示在这里~"
            )
        # 右栏：原网表内容
        with gr.Column():
            circuit_text = gr.Textbox(  # 重命名变量，避免和全局变量冲突
                label="原电路网表内容",
                lines=12,
                placeholder="网表内容会在这里展示~",
                interactive=False
            )

    res_text2 = gr.Textbox(label="大模型分析结果", lines=8, placeholder="点击分析，结果会显示在这里~")
    res_fig = gr.Plot(label="结果图表")

    # 分析按钮
    btn = gr.Button("开始分析", variant="primary", size="lg")

    # 关键修复：绑定输出增加circuit_text（右侧网表栏）
    btn.click(run_my_analysis, outputs=[res_text1, circuit_text, res_text2, res_fig])

# 启动工具（测试专用：单并发，仅本地访问）
if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",  # 仅本地访问，测试用
        server_port=7860,
        share=False,
        max_threads=1   # 强制单线程（测试专用）
    )