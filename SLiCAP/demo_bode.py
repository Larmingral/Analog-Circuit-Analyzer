import sys
import os
import matplotlib
matplotlib.use('Agg')
import SLiCAP as sl

os.makedirs("./cir", exist_ok=True)
os.makedirs("./html/css", exist_ok=True)
os.makedirs("./img", exist_ok=True)

start_f = float(sys.argv[1]) if len(sys.argv) > 1 else 0.001
stop_f = float(sys.argv[2]) if len(sys.argv) > 2 else 1000000
points = int(sys.argv[3]) if len(sys.argv) > 3 else 200

sl.initProject("Bode_Analysis")
sl.ini.disp = 0  # 关闭显示

cir = sl.makeCircuit("circuit.cir")
LaplaceResult = sl.doLaplace(cir, pardefs="circuit", numeric=True)

# 只要调用 plotSweep，SLiCAP 就会默认在 img/ 下生成同名的 .pdf 文件
sl.plotSweep("f_dBm", "dB Magnitude plot", LaplaceResult, start_f, stop_f, points,
             sweepScale="M", yUnits="V", funcType="dBmag")

sl.plotSweep("f_phs", "Phase plot", LaplaceResult, start_f, stop_f, points,
             sweepScale="M", yUnits="V", funcType="phase")

print("波特图运算完毕，PDF已成功生成！")