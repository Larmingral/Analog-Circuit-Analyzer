import re

# 全局支持的参数配置
MOS_PARAMS = ["cgs", "cgb", "cdg", "cdb", "csb", "gm", "gb", "go"]

def normalize_df(df_data):
    """【防死循环与非法行清洗】：彻底解决由于Gradio数据类型错乱引起的互相干扰"""
    if not df_data:
        return []
    norm = []
    for row in df_data:
        # 如果用户乱加了空行或没有元件名的行，直接丢弃
        if not row or not str(row[0]).strip():
            continue
        # 强制布尔解析：防止把 "False" 字符串解析成 True
        bools = [str(v).lower() in ['true', '1', 't', 'yes'] for v in row[1:]]
        norm.append([str(row[0]).strip()] + bools)
    return norm


def sync_text_to_df(netlist_text, current_df):
    """网表变动 -> 解析出最新状态填入表格"""
    if not netlist_text:
        return []

    rows = []
    lines = netlist_text.split('\n')
    for line in lines:
        line_stripped = line.strip()
        if line_stripped.upper().startswith('M'):
            tokens = line_stripped.split()
            if not tokens: continue
            inst_name = tokens[0]

            row = [inst_name]
            for p in MOS_PARAMS:
                has_param = any(t.startswith(f"{p}=") for t in tokens)
                row.append(has_param)
            rows.append(row)

    # 【死循环拦截】：深度比对清洗后的数据，如果没产生实际变化就不触发刷新
    if normalize_df(rows) == normalize_df(current_df):
        import gradio as gr
        return gr.update()
    return rows


def sync_df_to_text(df_data, current_text):
    """表格勾选 -> 精准改写网表"""
    if df_data is None:
        import gradio as gr
        return gr.update()

    norm_df = normalize_df(df_data)
    df_dict = {row[0]: row[1:] for row in norm_df}

    lines = current_text.split('\n')
    new_lines = []

    for line in lines:
        line_stripped = line.strip()
        if line_stripped.upper().startswith('M'):
            tokens = line_stripped.split()
            if not tokens: continue

            inst_name = tokens[0]
            if inst_name in df_dict:
                # 只剥离被我们管理的 MOS 参数，不影响网表原来的其他元素
                base_tokens = [t for t in tokens if not any(t.startswith(f"{p}=") for p in MOS_PARAMS)]

                suffix = re.sub(r'^[Mm]', '', inst_name)
                bool_vals = df_dict[inst_name]

                for i, p in enumerate(MOS_PARAMS):
                    if i < len(bool_vals) and bool_vals[i]:
                        base_tokens.append(f"{p}={{{p}{suffix}}}")

                new_lines.append(" ".join(base_tokens))
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    new_text = "\n".join(new_lines)

    # 【死循环拦截】
    if new_text.strip() == current_text.strip():
        import gradio as gr
        return gr.update()
    return new_text