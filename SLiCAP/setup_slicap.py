import SLiCAP

try:
    # ❌ 错误写法 (旧版本参数名):
    # SLiCAP.initProject(projectFileName='my_test_project')

    # ✅ 正确写法 (直接传字符串):
    SLiCAP.initProject('my_test_project')

    print("SLiCAP 初始化成功！")
except Exception as e:
    print(f"发生错误: {e}")