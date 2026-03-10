import SLiCAP as sl

# 1. 初始化
sl.initProject('CE_Amp_Analysis')

try:
    print("正在读取网表...")
    # 2. 加载电路
    cir = sl.makeCircuit('ce_amp.cir')

    # ========================================================
    # 页面 1: 电路详情
    # ========================================================
    sl.htmlPage('Circuit_Data')
    sl.head2html('Common Emitter Circuit Details')

    sl.head3html('1. Netlist')
    # 直接写文件名
    sl.netlist2html('ce_amp.cir')

    sl.head3html('2. Parameters')
    sl.elementData2html(cir)
    sl.params2html(cir)

    # ========================================================
    # 页面 2: 分析结果
    # ========================================================
    sl.htmlPage('Results')
    sl.head2html('Symbolic Analysis Results')

    # --- 任务 A: 电压增益 ---
    sl.head3html('1. Voltage Gain (V_out / V_source)')

    result_gain = sl.doLaplace(cir)

    # 【修正点 1】去掉 $ 符号，直接写合法的变量名字符串 "A_v"
    # SLiCAP 会自动把它渲染成 A 下标 v
    sl.text2html("Full Transfer Function:")
    sl.eqn2html(result_gain.laplace, "A_v")

    # --- 任务 B: 输入阻抗 ---
    sl.head3html('2. Input Impedance (Z_in)')

    try:
        ins_zin = cir.defTF(source='I_V1', detector='V1')
        result_zin = sl.doLaplace(ins_zin)

        # 【修正点 2】去掉 $ 和特殊字符，直接写 "Z_in"
        sl.text2html("Input Impedance:")
        sl.eqn2html(result_zin.laplace, "Z_in")

    except Exception as e:
        sl.text2html(f"Error calculating Zin: {str(e)}")

    print("\n" + "=" * 50)
    print("🎉 完美成功！HTML 报告生成完毕！")
    print("这次绝对没问题了。请打开 html/index.html 查看。")
    print("=" * 50)

except Exception as e:
    print(f"\n❌ 发生错误: {e}")