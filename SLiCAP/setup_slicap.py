import SLiCAP

try:
    SLiCAP.initProject('my_test_project')
    print("SLiCAP 初始化成功！")
except Exception as e:
    print(f"发生错误: {e}")