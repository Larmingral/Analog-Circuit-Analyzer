import SLiCAP as sl
sl.initProject('symbolic_analysis')
try:
    print("1")
    cir = sl.makeCircuit('my_circuit.cir')
    print("2")
    result = sl.doLaplace(cir)
    print("\n" + "=" * 40)
    print("分析结果 (Vout/Vin):")
    print(result.laplace)
    print("=" * 40 + "\n")

except AttributeError as e:
    print(f"属性错误: {e}")
except Exception as e:
    print(f"其他错误: {e}")