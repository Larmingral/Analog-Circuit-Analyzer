import os
import subprocess
from dashscope import Generation

# 替换为你自己的文本
result = subprocess.run(['python', 'test_slicap.py'], capture_output=True, text=True)
with open("./cir/my_circuit.cir", "r", encoding="utf-8") as f:  # 替换为你的文件路径
    file_content = f.read()
output_text = result.stdout

messages = [
    {'role': 'system', 'content': '你是一个电路分析的助手，请根据网表和生成的分析结果，对电路性能进行一个简要的分析和概述。'},
    {'role': 'user', 'content': f'请分析以下结果：{output_text},电路网表是{file_content}'}
]

response = Generation.call(
    api_key="sk-0a85c32631604fb496aa4a4152f323e5",  # 从环境变量读取API Keyos.getenv("DASHSCOPE_API_KEY")
    model="qwen-plus",  # 推荐入门使用 qwen-plus
    messages=messages,
    result_format="message"
)

if response.status_code == 200:
    print("分析结果：")
    print(response.output.choices[0].message.content)
else:
    print(f"出错了：{response.message}")