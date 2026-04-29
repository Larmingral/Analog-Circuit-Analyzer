import SLiCAP as sl
import shutil

#创建slicap项目
sl.initProject("nmos common source")

cirName = "circuit"
fileName = cirName + ".cir"

dst = "cir"

#创建电路对象
cir = sl.makeCircuit(fileName)

#电路矩阵
MNA = sl.doMatrix(cir)
sl.htmlPage("Matrix Equations")
sl.matrices2html(MNA, label="MNA", labelText="MNA equation of the network")



