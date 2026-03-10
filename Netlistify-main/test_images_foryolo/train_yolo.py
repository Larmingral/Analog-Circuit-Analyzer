from ultralytics import YOLO

def train():
    # 1. 加载一个预训练的最小模型 (Nano版本，速度快)
    # 它会自动下载 yolov8n.pt，不用担心
    model = YOLO("yolov8n.pt")

    # 2. 开始训练
    # data: 指向你刚才建的 data.yaml
    # epochs: 训练几轮。CPU建议设为 3-5 先跑通流程。如果以后有显卡了可以设 100。
    # imgsz: 图片大小，电路图通常比较大，但在 CPU 上为了速度可以设小点，比如 640
    results = model.train(data="data.yaml", epochs=5, imgsz=640, device='cpu')

    # 3. 训练完成后，它会告诉你最佳模型保存在哪里
    # 通常在 runs/detect/train/weights/best.pt
    print("训练完成！模型已保存。")

if __name__ == '__main__':
    train()