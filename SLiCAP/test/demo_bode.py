import SLiCAP as sl
import shutil

#创建slicap项目
sl.initProject("demo")

cirName = "circuit_bode"
fileName = cirName + ".cir"

dst = "../cir"

#创建电路对象
cir = sl.makeCircuit(fileName)

#电路矩阵
MNA = sl.doMatrix(cir)
sl.htmlPage("Matrix Equations")
sl.matrices2html(MNA, label="MNA", labelText="MNA equation of the network")

#拉普拉斯变换
result = sl.doLaplace(cir)
gain = result.laplace
sl.htmlPage("Laplace Transfer")
sl.eqn2html("gain", gain)

#零极点分析
sl.htmlPage("pole-zero analysis")
poles = sl.doPoles(cir).poles
zeros = sl.doZeros(cir).zeros
sl.eqn2html("poles", poles)
sl.eqn2html("zeros", zeros)

#绘制波特图
LaplaceResult = sl.doLaplace(cir, pardefs="circuit", numeric=True)

sl.htmlPage("Plot1")
#Magnitude
f_dBm = sl.plotSweep("f_dBm", "dB Magnitude plot", LaplaceResult, 0.001, 1000000, 200,
                     sweepScale="M", yUnits="V", funcType="dBmag")

#Phase
f_phs = sl.plotSweep("f_phs", "Phase plot", LaplaceResult, 0.001, 1000000, 200,
                     sweepScale="M", yUnits="V", funcType="phase")

sl.fig2html(f_dBm, 800)

sl.htmlPage("Plot2")
sl.fig2html(f_phs, 800)