import SLiCAP as sl
import shutil

#创建slicap项目
sl.initProject("demo_5")

#将.cir电路网表文件移动至cir文件夹

cirName = "RLC circuit"
fileName = cirName + ".cir"

dst = "cir"

shutil.move(fileName, dst)

#创建电路对象
cir = sl.makeCircuit(fileName)

#电路矩阵
MNA = sl.doMatrix(cir)
sl.htmlPage("Matrix Equations")
sl.matrices2html(MNA, label="MNA", labelText="MNA equation of the network")


#拉普拉斯变换
result = sl.doLaplace(cir)
gain = result.laplace
vout_laplace = sl.doLaplace(cir, transfer=None).laplace


#格式化输出等式
sl.htmlPage("Laplace Transfer")
sl.eqn2html("V_out/V_in", gain, label='gainLaplace', labelText='Laplace transfer function')
sl.eqn2html("v_out", vout_laplace)
