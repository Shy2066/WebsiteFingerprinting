import numpy as np
import os
import argparse

"""
将防御机制输出文件夹中的轨迹按有效长度进行分类，并保存为NPZ文件
假设防御输出文件夹中的每个文件名格式为: label-instance (无后缀)
文件内容为每行 "timestamp\t direction"
输入文件夹路径，例如 'CW_10percent_input_res'
输出 NPZ 文件路径，例如 'CW_10percent_wtfpad.npz'
命令：python defense_folder_to_npz.py --input_folder /home/shy/Project/WebsiteFingerprinting/defenses/results/tor_fiber_wtfpad --output_npz /home/shy/Project/Website-Fingerprinting-Library/datasets/WFdata75x80/tor_fiber_wtfpad.npz
"""
def defense_folder_to_npz(input_folder, output_npz):
    files = [f for f in os.listdir(input_folder) if os.path.isfile(os.path.join(input_folder, f))]
    traces = []
    labels = []

    # 首先遍历所有文件以确定最大长度
    max_len = 0
    for file in files:
        filepath = os.path.join(input_folder, file)
        with open(filepath, 'r') as f:
            trace_length = len([line for line in f])
            max_len = max(max_len, trace_length)

    print(f"检测到的最大轨迹长度: {max_len}")

    for file in files:
        label, instance = map(int, file.split('-'))  # 假设 '标签-实例' 格式
        filepath = os.path.join(input_folder, file)

        trace = []
        with open(filepath, 'r') as f:
            for line in f:
                timestamp, direction = line.strip().split('\t')
                trace.append(int(direction))  # 收集方向；如果攻击不需要时间戳，则忽略

        # 用零填充至 max_len
        padded_trace = np.zeros(max_len, dtype=int)
        if len(trace) <= max_len:
            padded_trace[:len(trace)] = trace
        else:
            # 如果轨迹长度超过max_len（理论上不应该发生，但作为安全措施）
            padded_trace = np.array(trace[:max_len])

        traces.append(padded_trace)
        labels.append(label)

    X = np.array(traces)
    y = np.array(labels)

    np.savez(output_npz, X=X, y=y)
    print(f"已将 {input_folder} 转换为 {output_npz}，形状 X: {X.shape}，y: {y.shape}。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="将防御输出文件夹转换为 NPZ 文件。")
    parser.add_argument("--input_folder", type=str, required=True, help="输入文件夹路径，例如 'CW_10percent_input_res'")
    parser.add_argument("--output_npz", type=str, required=True, help="输出 NPZ 文件路径，例如 'CW_10percent_wtfpad.npz'")
    args = parser.parse_args()

    defense_folder_to_npz(args.input_folder, args.output_npz)