import SLiCAP as sl
import shutil

#创建slicap项目
sl.initProject("nmos common source")

cirName = "circuit"
fileName = cirName + ".cir"

dst = "cir"

#创建电路对象
cir = sl.makeCircuit(fileName)

#拉普拉斯变换
result = sl.doLaplace(cir)
gain = result.laplace
sl.htmlPage("Laplace Transfer")
sl.eqn2html("gain", gain)




