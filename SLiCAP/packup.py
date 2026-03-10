import gradio as gr
import os
import subprocess
import matplotlib.pyplot as plt
from dashscope import Generation

# 要运行的脚本文件名
aaa = "test_slicap.py"
# 全局变量存储大模型分析结果（解决作用域问题）
llm_analysis_result = ""
file_content = ""

def run_my_analysis():
    """核心分析函数：运行脚本 + 调用大模型 + 生成图表"""
    global llm_analysis_result
    llm_analysis_result = ""  # 每次运行先清空

    # 1. 运行外部Python脚本，捕获输出和错误
    # 修复：shell=True时命令要传字符串，且统一编码避免乱码
    result = subprocess.run(
        f"python {aaa}",  # shell=True时用字符串格式
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="ignore"  # 忽略编码错误，避免程序崩溃
    )

    # 整理脚本运行结果
    analysis_result = result.stdout
    if result.stderr:
        analysis_result += f"\n\n【程序运行提示】：{result.stderr}"

    # 2. 读取电路网表文件
    try:
        with open("./cir/my_circuit.cir", "r", encoding="utf-8") as f:
            file_content = f.read()
    except FileNotFoundError:
        analysis_result += "\n\n【警告】：未找到电路网表文件 ./cir/my_circuit.cir，请检查路径！"
        file_content = ""
    except Exception as e:
        analysis_result += f"\n\n【文件读取错误】：{str(e)}"
        file_content = ""

    # 3. 调用通义千问大模型分析结果
    if file_content and analysis_result.strip():
        messages = [
            {'role': 'system',
             'content': '你是一个电路分析的助手，请根据网表和生成的分析结果，对电路性能进行一个简要的分析和概述，语言简洁明了。'},
            {'role': 'user', 'content': f'请分析以下电路分析结果：{analysis_result}\n\n对应的电路网表是：{file_content}'}
        ]

        try:
            response = Generation.call(
                api_key="sk-0a85c32631604fb496aa4a4152f323e5",
                # api_key=os.getenv("DASHSCOPE_API_KEY"),
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


    fig = plt.figure(figsize=(6, 3))
    plt.text(0.5, 0.5, "分析数据图表（后续可替换）", ha="center", fontsize=12)
    plt.axis("off")

    plt.close(fig)
    return analysis_result, llm_analysis_result, fig


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
            file_content = gr.Textbox(
                label="原电路网表内容",
                lines=12,
                placeholder="网表内容会在这里展示~",
                interactive=False  # 设为只读，避免用户修改
            )

    res_text2 = gr.Textbox(label="大模型分析结果", lines=8, placeholder="点击分析，结果会显示在这里~")
    res_fig = gr.Plot(label="结果图表")  # 后续加图表直接用

    # 分析按钮
    btn = gr.Button("开始分析", variant="primary", size="lg")

    # 绑定按钮事件：点击后运行分析函数，输出三个结果
    btn.click(run_my_analysis, outputs=[res_text1, res_text2, res_fig])

# 启动工具
if __name__ == "__main__":
    # 可选：设置share=True生成公网链接，server_port指定端口
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        max_threads=16
    )