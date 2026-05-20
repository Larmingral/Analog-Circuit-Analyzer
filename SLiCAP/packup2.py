import gradio as gr
from netlist_parser import sync_text_to_df, sync_df_to_text, update_param_df, MOS_PARAMS
from analysis import run_my_analysis

DEFAULT_NETLIST = """Vdd Vdd 0 V dc={Vdd} value=0
Vin in 0 V value={Vin} 

Rd Vdd out R value={Rd}
Rs net1 0 R value={Rs}

M1 out in net1 0 M gm={gm1} cgs={cgs1} cdg={cdg1}

.source Vin
.detector V_out
.end"""

with gr.Blocks(theme=gr.themes.Soft(), title="智能电路分析系统") as demo:
    gr.Markdown("## 📝 智能电路图识别与一键分析工具")

    gr.Markdown("### 📸 第一步：输入电路图与网表生成")
    with gr.Row():
        with gr.Column(scale=1):
            img_input = gr.Image(sources=["upload", "webcam"], type="filepath", label="1. 拍摄或上传")
            btn_img_to_netlist = gr.Button("⚡ 识别图片提取网表 (功能预留)")
        with gr.Column(scale=1):
            circuit_text = gr.Textbox(lines=12, label="2. 可编辑电路网表", value=DEFAULT_NETLIST, interactive=True)

    gr.Markdown("---")

    gr.Markdown("### ⚙️ 第二步：元件参数提取与赋值配置")
    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("#### A. MOS管小信号参数 (打钩自动插入网表)")
            mos_df = gr.Dataframe(
                value=sync_text_to_df(DEFAULT_NETLIST, []),
                headers=["MOS元件"] + MOS_PARAMS, datatype=["str"] + ["bool"] * len(MOS_PARAMS),
                type="array", interactive=True, row_count=(1, "dynamic"), col_count=(len(MOS_PARAMS) + 1, "fixed")
            )

        with gr.Column(scale=1):
            gr.Markdown("#### B. 核心变量具体赋值 (后台自动注入 .param)")
            param_df = gr.Dataframe(
                value=update_param_df(DEFAULT_NETLIST, []),
                headers=["参数名 (变量)", "具体数值"], datatype=["str", "str"],
                type="array", interactive=True, row_count=(1, "dynamic"), col_count=(2, "fixed")
            )

    gr.Markdown("---")

    gr.Markdown("### 🚀 第三步：选择分析类型并执行")
    with gr.Row():
        analysis_selector = gr.CheckboxGroup(
            choices=["拉普拉斯分析", "矩阵方程分析", "波特图绘制"],
            value=["拉普拉斯分析", "波特图绘制"],
            label="请勾选需要运行的独立模块", interactive=True
        )

        with gr.Accordion("📶 波特图扫频参数设置 (选填)", open=False):
            with gr.Row():
                sweep_start = gr.Number(value=0.001, label="起始频率 (Hz)")
                sweep_stop = gr.Number(value=1e6, label="终止频率 (Hz)")
                sweep_points = gr.Number(value=200, label="扫描点数", precision=0)

    btn_analyze = gr.Button("开始综合分析", variant="primary", size="lg")

    gr.Markdown("---")

    # ... 前半部分代码不变 ...

    gr.Markdown("### 📊 第四步：分析结果")
    out_laplace = gr.Markdown(visible=False, label="拉普拉斯传递函数")
    out_matrix = gr.Markdown(visible=False, label="矩阵方程")

    # 采用原生的 gr.Image 接收 PNG，既不会卡死浏览器，右上角又自带全屏放大与下载按钮
    with gr.Row():
        out_bode_mag = gr.Image(type="filepath", visible=False, label="波特幅度图 (高清PNG)", interactive=False)
        out_bode_phs = gr.Image(type="filepath", visible=False, label="波特相位图 (高清PNG)", interactive=False)

    gr.Markdown("#### 🤖 大模型深度分析结果")
    res_markdown = gr.Markdown(
        value="大模型根据公式推导的分析结果会显示在这里~",
        latex_delimiters=[
            {"left": "$$", "right": "$$", "display": True},
            {"left": r"\(", "right": r"\)", "display": False},
            {"left": "$", "right": "$", "display": False},
            {"left": "\\[", "right": "\\]", "display": False}
        ]
    )
    res_fig = gr.Plot(visible=False)

    # ---------------- 事件绑定 ----------------
    btn_img_to_netlist.click(fn=lambda x: DEFAULT_NETLIST, inputs=[img_input], outputs=[circuit_text])
    circuit_text.change(fn=sync_text_to_df, inputs=[circuit_text, mos_df], outputs=[mos_df])
    circuit_text.change(fn=update_param_df, inputs=[circuit_text, param_df], outputs=[param_df])
    mos_df.change(fn=sync_df_to_text, inputs=[mos_df, circuit_text], outputs=[circuit_text])

    btn_analyze.click(
        fn=run_my_analysis,
        inputs=[circuit_text, param_df, analysis_selector, sweep_start, sweep_stop, sweep_points],
        outputs=[out_laplace, out_matrix, out_bode_mag, out_bode_phs, res_markdown, res_fig]
    )

if __name__ == "__main__":
    # 【核心修改】：去掉了 max_threads=1，防止阻塞浏览器的网络心跳检测！
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)