import os
import subprocess
import matplotlib.pyplot as plt
import gradio as gr
from dashscope import Generation
from utils import read_file_content, get_latest_html, parse_slicap_to_markdown


def run_my_analysis(ui_netlist_text, analysis_types):
    if not ui_netlist_text or not analysis_types:
        return (gr.update(visible=False), gr.update(visible=False), "⚠️ 分析失败：未提供网表或未勾选分析项！", None)

    # 1. 写入最新的网表
    os.makedirs("./cir", exist_ok=True)
    with open("./cir/circuit.cir", "w", encoding="utf-8") as f:
        f.write(ui_netlist_text)

    md_laplace, md_matrix, llm_context = "", "", ""
    os.makedirs("./html", exist_ok=True)

    is_laplace_selected = "拉普拉斯分析" in analysis_types
    is_matrix_selected = "矩阵方程分析" in analysis_types

    # 2. 执行并寻找最新的拉普拉斯文件
    if is_laplace_selected:
        subprocess.run("python run_laplace.py", shell=True, errors="ignore")
        latest_lap = get_latest_html("./html", "Laplace-Transfer.html")
        if latest_lap:
            raw_laplace = read_file_content(latest_lap)
            md_laplace = parse_slicap_to_markdown(raw_laplace)
            llm_context += f"--- 传递函数 (来源文件: {os.path.basename(latest_lap)}) ---\n{md_laplace}\n\n"
        else:
            md_laplace = "*⚠️ 目录中未找到符合 Laplace-Transfer.html 结尾的结果文件*"

    # 3. 执行并寻找最新的矩阵方程文件
    if is_matrix_selected:
        subprocess.run("python run_matrix.py", shell=True, errors="ignore")
        latest_mat = get_latest_html("./html", "Matrix-Equations.html")
        if latest_mat:
            raw_matrix = read_file_content(latest_mat)
            md_matrix = parse_slicap_to_markdown(raw_matrix)
            llm_context += f"--- 矩阵方程 (来源文件: {os.path.basename(latest_mat)}) ---\n{md_matrix}\n\n"
        else:
            md_matrix = "*⚠️ 目录中未找到符合 Matrix-Equations.html 结尾的结果文件*"

    # 4. 【核心改进】：根据勾选项，动态构建给大模型的 Prompt
    expected_sections = ["### 一、 电路拓扑与基础分析\n（必须使用 Markdown 表格归纳）"]
    section_index = 2

    if is_laplace_selected:
        expected_sections.append(
            f"### {['一', '二', '三', '四', '五'][section_index - 1]}、 拉普拉斯传递函数 (Laplace Transfer)\n（请先使用块级公式 `$$...$$` 渲染传入的传递函数，再结合网表参数详细分析其增益特性、零极点分布等）")
        section_index += 1

    if is_matrix_selected:
        expected_sections.append(
            f"### {['一', '二', '三', '四', '五'][section_index - 1]}、 节点电压矩阵方程 (Matrix Equations)\n（请先使用块级公式 `$$...$$` 渲染传入的矩阵方程，再解释矩阵维度及对应元素的物理联系）")
        section_index += 1

    expected_sections.append(
        f"### {['一', '二', '三', '四', '五'][section_index - 1]}、 综合性能评估\n（一到两句话总结整体性能或潜在应用场景）")

    dynamic_prompt_sections = "\n\n".join(expected_sections)

    # 5. 调用大模型
    llm_analysis_result = ""
    if llm_context.strip():
        messages = [
            {'role': 'system', 'content': (
                "你是一位顶级的电子电路分析专家。我将为你提供电路网表及提取的公式。\n"
                "请你**务必严格按照以下模块的顺序和格式**进行输出：\n\n"
                f"{dynamic_prompt_sections}\n\n"
                "⚠️ 【极度重要的排版规范】：\n"
                 "为了防止 Markdown 解析引擎冲突，正文中的**所有行内变量、带下标的符号**（例如跨导 \\(g_m\\)、电阻 \\(R_l\\)、基极电阻 \\(r_\\pi\\) 等），**绝对禁止使用单美元符号 `$ ... $` 包裹**，请**务必全部使用 `\\( ... \\)` 来包裹**！\n"
                 "（正确示例：通过调节 \\(g_m\\) 和 \\(R_l\\) 的阻值...；错误示例：通过调节 $g_m$ 和 $R_l$ 的阻值...）"
            )},
            {'role': 'user', 'content': f"【提取的公式内容】：\n{llm_context}\n\n【原电路网表内容】：\n{ui_netlist_text}"}
        ]
        try:
            response = Generation.call(
                api_key=os.environ.get("DASHSCOPE_API_KEY"),
                model="qwen-plus", messages=messages, result_format="message"
            )
            if response.status_code == 200:
                llm_analysis_result = response.output.choices[0].message.content
            else:
                llm_analysis_result = f"大模型调用失败：{response.message}"
        except Exception as e:
            llm_analysis_result = f"大模型异常：{str(e)}"
    else:
        llm_analysis_result = "⚠️ 提取有效公式失败，大模型终止分析。"

    # 生成占位图表
    fig = plt.figure(figsize=(8, 4))
    plt.text(0.5, 0.5, f"运行完毕：{', '.join(analysis_types)}", ha="center", fontsize=12)
    plt.axis("off")
    plt.close(fig)

    return (
        gr.update(value=md_laplace, visible=is_laplace_selected),
        gr.update(value=md_matrix, visible=is_matrix_selected),
        llm_analysis_result,
        fig
    )