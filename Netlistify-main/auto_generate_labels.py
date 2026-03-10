import os
import shutil
from ultralytics import YOLO
from pathlib import Path

# ================= 配置区域 =================
# 1. 你的 YOLO 模型路径 (请确保 weights 文件夹里有 best.pt)
#    注意：这里必须是用 YOLOv8 训练出来的那个 .pt 文件
model_path = "test_images_foryolo/runs/detect/train6/weights/best.pt"

# 2. 你的测试图片文件夹
source_dir = "test_images_own/images"

# 3. 标签保存的目标文件夹 (Netlistify 代码读取标签的地方)
target_label_dir = "data/test_images/labels"


# ===========================================

def generate_labels():
    print(f"正在加载模型: {model_path} ...")
    try:
        model = YOLO(model_path)
    except Exception as e:
        print(f"错误：无法加载模型。请确认路径是否正确，或者是否安装了 ultralytics。\n{e}")
        return

    print(f"开始对 {source_dir} 进行检测...")

    # 使用 YOLO 进行预测
    # save_txt=True: 生成 txt 标签
    # conf=0.25: 置信度阈值，如果识别漏了可以调低这个数
    results = model.predict(source=source_dir, save=True, save_txt=True, conf=0.25, project="runs/detect",
                            name="temp_predict", exist_ok=True)

    # 预测结果通常保存在 runs/detect/temp_predict/labels 下
    generated_labels_dir = Path("runs/detect/temp_predict/labels")

    if not generated_labels_dir.exists():
        print("警告：模型没有检测到任何物体，或者没有生成 labels 文件夹。请检查图片或降低 conf 阈值。")
        return

    # 确保目标文件夹存在
    Path(target_label_dir).mkdir(parents=True, exist_ok=True)

    print("正在将生成的标签移动到项目目录...")
    # 遍历生成的文件并移动
    count = 0
    for label_file in generated_labels_dir.glob("*.txt"):
        shutil.copy(label_file, Path(target_label_dir) / label_file.name)
        count += 1

    print(f"成功！已生成 {count} 个标签文件到 {target_label_dir}。")
    print("现在你可以运行 inference.py 了。")


if __name__ == "__main__":
    generate_labels()