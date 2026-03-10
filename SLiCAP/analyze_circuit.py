# 导入 SLiCAP 库
from SLiCAP import *

# 创建一个 SLiCAP 项目
initProject("CommonEmitterAnalysis")

# 从网表文件创建一个电路对象
circuit = makeCircuit("common_emitter.cir")

# 1. 直流工作点分析 (DC Operating Point Analysis)
print("--- 直流工作点分析 ---")
# 使用正确的函数名 DC 并传入 circuit 对象
op_points = DC(circuit)
print(op_points)

# 2. 交流频率响应分析 (AC Frequency Response Analysis)
print("\n--- 交流频率响应分析 ---")
# 定义分析的频率范围从 1Hz 到 100MHz
ac_analysis = sweep(circuit, "AC", "VIN", "V(OUT)", start="1", stop="100M", num=1000, scale="log")

# 计算中频增益
gain_db = ac_analysis.getGain(unit="dB")
# 获取频率为 10kHz 时的增益值
mid_band_gain = gain_db.getValue(10e3)
print(f"中频电压增益 (在 10kHz): {mid_band_gain:.2f} dB")

# 绘制伯德图 (Bode Plot)
plotSweep(gain_db, title="Frequency Response - Gain", xlog=True, ylog=False, grid=True)
plotSweep(ac_analysis.getPhase(), title="Frequency Response - Phase", xlog=True, ylog=False, grid=True)

# 3. 瞬态分析 (Transient Analysis)
print("\n--- 瞬态分析 ---")
# 定义分析的时间范围为 0 到 3ms，步长为 1us
# 使用正确的函数名 transient 并传入 circuit 对象
tran_analysis = transient(circuit, tstart=0, tstop="3m", tstep="1u")

# 绘制输入和输出波形
plotTran(tran_analysis, signals=["V(IN)", "V(OUT)"], title="Transient Analysis - Input vs Output", grid=True)

# 显示所有绘图
show()