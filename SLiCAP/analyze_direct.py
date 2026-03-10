import SLiCAP as sl

# 1. 初始化项目
sl.initProject('Direct_CE_Analysis')

try:
    print("正在读取直接耦合电路网表...")
    cir = sl.makeCircuit('direct_ce.cir')

    # ==========================================
    # 创建 HTML 报告
    # ==========================================
    sl.htmlPage('Direct_Coupled_Results')
    sl.head2html('Direct Coupled CE Amplifier Analysis')

    # 1. 展示网表
    sl.head3html('1. Circuit Netlist')
    sl.text2html('Note: No capacitors are present. Re introduces negative feedback.')
    sl.netlist2html('direct_ce.cir')

    # 2. 展示参数
    sl.head3html('2. Parameters')
    sl.params2html(cir)

    # ==========================================
    # 任务 A: 电压增益 (DC Gain)
    # ==========================================
    sl.head3html('3. Voltage Gain (V_c / V_in)')
    sl.text2html('Since there are no capacitors, this is a DC gain (frequency independent).')
    sl.text2html('Notice the effect of Re in the denominator (Emitter Degeneration).')

    # 执行分析
    result_gain = sl.doLaplace(cir)

    # 渲染公式 (变量名为 A_v)
    sl.eqn2html(result_gain.laplace, "A_v")

    # ==========================================
    # 任务 B: 输入阻抗
    # ==========================================
    sl.head3html('4. Input Impedance (Z_in)')
    sl.text2html('With Re present, the input impedance should increase significantly:')
    sl.text2html('Z_in approx r_pi + (beta + 1) * Re')

    try:
        # 定义输入阻抗: V_b / I_V1 (假设 Rs 很小，或者直接看 V_in 处的阻抗)
        # 这里我们要看从 V1 发出的电流看到的阻抗
        ins_zin = cir.defTF(source='I_V1', detector='V1')
        result_zin = sl.doLaplace(ins_zin)

        sl.eqn2html(result_zin.laplace, "Z_in")
    except Exception as e:
        sl.text2html(f"Error: {str(e)}")

    print("\n" + "=" * 50)
    print("🎉 分析完成！")
    print("请查看 html/index.html")
    print("预期结果：你会发现增益公式中没有 's' 变量，且分母中出现了 gm*Re 项。")
    print("=" * 50)

except Exception as e:
    print(f"\n❌ 发生错误: {e}")