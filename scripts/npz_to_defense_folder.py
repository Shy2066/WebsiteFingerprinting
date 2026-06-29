import numpy as np
import os

"""
将NPZ文件转换为防御机制输出文件夹格式
假设NPZ文件包含 'X' (shape: (样本数, 序列长度)) 和 'y' (shape: (样本数,)) 两个数组
每个样本的有效长度定义为非零元素的最后一个索引 + 1
输出文件夹中的每个文件名格式为: label-instance (无后缀)
文件内容为每行 "timestamp\t direction"
"""
def npz_to_defense_folder(npz_file, output_folder):
    # 加载 NPZ 文件
    data = np.load(npz_file)
    X = data['X']  # 形状：(样本数, 序列长度)，例如 (N, 10000)
    y = data['y']  # 形状：(N,)

    # 如果输出文件夹不存在，则创建
    os.makedirs(output_folder, exist_ok=True)

    # 按标签分组轨迹，以分配实例编号
    labels = np.unique(y)
    instance_counters = {label: 0 for label in labels}

    for i in range(len(y)):
        label = y[i]
        instance = instance_counters[label]
        filename = f"{label}-{instance}"
        filepath = os.path.join(output_folder, filename)

        # 提取轨迹的非零部分（有效长度）
        trace = X[i]
        nonzero_idx = np.nonzero(trace)[0]
        effective_trace = trace[:nonzero_idx[-1] + 1] if len(nonzero_idx) > 0 else trace

        # 将轨迹写入文件，以时间戳\t方向形式；假设 X 为方向序列（+1/-1），时间戳使用索引作为占位符；如果数据中包含实际时间戳，请调整
        with open(filepath, 'w') as f:
            for idx, direction in enumerate(effective_trace):
                if direction != 0:  # 跳过零值，但根据任务，有效长度排除尾部零
                    f.write(f"{idx:.4f}\t{int(direction)}\n")  # 使用索引作为时间戳占位符；如需实际时间戳，请替换

        instance_counters[label] += 1

    print(f"已将 {npz_file} 转换为文件夹：{output_folder}，包含 {len(y)} 个文件。")

# 示例用法（针对一个子数据集）
# npz_to_defense_folder('CW_10percent.npz', 'CW_10percent_input')