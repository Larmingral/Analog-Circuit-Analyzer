import gradio as gr
from netlist_parser import sync_text_to_df, sync_df_to_text, MOS_PARAMS
from analysis import run_my_analysis

# --- 在这里定义网页刚打开时的默认网表 ---
DEFAULT_NETLIST = """Vdd Vdd 0 V dc={Vdd} value=0

Vin in 0 V value={Vin} 

Rd Vdd out R value={Rd}
Rs net1 0 R value={Rs}

M1 out in net1 0 M gm={gm1} cgs={cgs1} cdg={cdg1}

.source Vin
.detector V_out
.end"""


def mock_image_to_netlist(image_path):
    if not image_path: return "请先上传图片！"
    # 当用户点击预留的识别按钮时，依然可以返回这个默认网表用于测试
    return DEFAULT_NETLIST


with gr.Blocks(theme=gr.themes.Soft(), title="智能电路分析系统") as demo:
    gr.Markdown("## 📝 智能电路图识别与一键分析工具")

    gr.Markdown("### 📸 第一步：输入电路图与网表生成")
    with gr.Row():
        with gr.Column(scale=1):
            img_input = gr.Image(sources=["upload", "webcam", "clipboard"], type="filepath",
                                 label="1. 拍摄或上传电路图")
            btn_img_to_netlist = gr.Button("⚡ 识别图片提取网表 (功能预留)", variant="secondary")

        with gr.Column(scale=1):
            # 【改进点 1】：加入 value=DEFAULT_NETLIST，一打开网页就默认填入
            circuit_text = gr.Textbox(
                lines=12,
                label="2. 可编辑电路网表",
                value=DEFAULT_NETLIST,
                interactive=True
            )

    gr.Markdown("---")

    gr.Markdown("### ⚙️ 第二步：MOS 管参数实时配置")
    gr.Markdown(
        "*注意：由于组件特性，表格允许您增加或删除行。这**不会引起系统错误**，系统后台会自动过滤并丢弃无效的干扰行，您只需专注勾选参数即可。*")

    # 【改进点 2】：利用我们写的 sync_text_to_df 函数，在页面渲染前直接算出默认表格状态，并填入 value
    initial_df_state = sync_text_to_df(DEFAULT_NETLIST, [])

    # 强制固定列宽(col_count=(9, "fixed"))，禁止乱加列
    mos_df = gr.Dataframe(
        value=initial_df_state,
        headers=["MOS元件"] + MOS_PARAMS,
        datatype=["str"] + ["bool"] * len(MOS_PARAMS),
        type="array",
        interactive=True,
        row_count=(1, "dynamic"),
        col_count=(len(MOS_PARAMS) + 1, "fixed")
    )

    gr.Markdown("---")

    gr.Markdown("### 🚀 第三步：选择分析类型并执行")
    analysis_selector = gr.CheckboxGroup(
        choices=["拉普拉斯分析", "矩阵方程分析"],
        value=["拉普拉斯分析"],
        label="请勾选需要运行的独立模块",
        interactive=True
    )
    btn_analyze = gr.Button("开始综合分析", variant="primary", size="lg")

    gr.Markdown("---")

    gr.Markdown("### 📊 第四步：分析结果")
    out_laplace = gr.Markdown(visible=False, label="拉普拉斯传递函数")
    out_matrix = gr.Markdown(visible=False, label="矩阵方程")

    gr.Markdown("#### 🤖 大模型深度分析结果")
    res_markdown = gr.Markdown(
        value="大模型根据公式推导的分析结果会显示在这里~",
        latex_delimiters=[
            {"left": "$$", "right": "$$", "display": True},
            {"left": r"\(", "right": r"\)", "display": False},
            {"left": "$", "right": "$", "display": False},
            {"left": "[", "right": "]", "display": False}
        ]
    )

    res_fig = gr.Plot()

    # 事件绑定
    btn_img_to_netlist.click(fn=mock_image_to_netlist, inputs=[img_input], outputs=[circuit_text])
    circuit_text.change(fn=sync_text_to_df, inputs=[circuit_text, mos_df], outputs=[mos_df])
    mos_df.change(fn=sync_df_to_text, inputs=[mos_df, circuit_text], outputs=[circuit_text])
    btn_analyze.click(
        fn=run_my_analysis,
        inputs=[circuit_text, analysis_selector],
        outputs=[out_laplace, out_matrix, res_markdown, res_fig]
    )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)