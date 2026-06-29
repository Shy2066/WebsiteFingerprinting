import numpy as np
import os
import argparse
from collections import defaultdict

"""
将防御机制输出文件夹中的轨迹按有效长度进行分类，并保存为NPZ文件
假设防御输出文件夹中的每个文件名格式为: label-instance (无后缀)
文件内容为每行 "timestamp\t direction"
"""
def load_traces_from_defense_folder(folder_path):
    """
    从防御输出文件夹加载所有轨迹和标签。
    文件名格式: label-instance (无后缀)
    文件内容: 每行 "timestamp\t direction"
    """
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    files.sort()  # 确保顺序一致，便于复现

    traces = []
    labels = []
    file_names = []

    print(f"从文件夹 {folder_path} 加载 {len(files)} 条轨迹...")

    for file in files:
        label_str, instance_str = file.split('-')
        label = int(label_str)

        filepath = os.path.join(folder_path, file)
        trace = []

        with open(filepath, 'r') as f:
            for line in f:
                if line.strip():
                    _, direction = line.strip().split('\t')
                    trace.append(int(direction))

        traces.append(np.array(trace, dtype=int))
        labels.append(label)
        file_names.append(file)

    return traces, np.array(labels), file_names

def compute_effective_lengths(traces):
    """
    计算每条轨迹的有效长度（最后一个非零位置 + 1）
    """
    lengths = np.zeros(len(traces), dtype=int)
    for i, trace in enumerate(traces):
        nonzero = np.nonzero(trace)[0]
        if len(nonzero) > 0:
            lengths[i] = nonzero[-1] + 1
        else:
            lengths[i] = 0  # 全零轨迹
    return lengths

def main():
    parser = argparse.ArgumentParser(description="从防御输出文件夹生成按有效长度排序的子数据集")
    parser.add_argument("--input_folder", type=str, required=True,
                        help="防御机制输出文件夹路径（如 CW_front_res）")
    parser.add_argument("--output_folder", type=str, default="/home/shy/Project/Website-Fingerprinting-Library/datasets",
                        help="输出文件夹路径，默认为当前目录")
    parser.add_argument("--max_len", type=int, default=6000,
                        help="填充到固定长度（建议 30000 或更大，以容纳防御后长序列）")
    parser.add_argument("--min_samples_per_class", type=int, default=0,
                        help="每个类别最少样本数，少于此数的类别将被移除")
    args = parser.parse_args()

    input_folder = args.input_folder.rstrip('/')
    base_name = os.path.basename(input_folder)
    
    # 确保输出文件夹存在
    os.makedirs(args.output_folder, exist_ok=True)

    # 1. 加载所有轨迹
    traces_list, y, file_names = load_traces_from_defense_folder(input_folder)
    N = len(y)
    print(f"加载完成，总样本数: {N}, 原始类别数: {len(np.unique(y))}")

    # 2. 计算有效长度并排序
    lengths = compute_effective_lengths(traces_list)
    sorted_indices = np.argsort(lengths)  # 从小到大
    lengths_sorted = lengths[sorted_indices]

    # 3. 循环生成 10% ~ 50% 子数据集
    # percentiles = [10, 20, 30, 40, 50]
    percentiles = [100]
    for p in percentiles:
        n_keep = int(N * p / 100)
        if n_keep == 0:
            continue

        min_len = lengths_sorted[0]
        max_len = lengths_sorted[n_keep - 1]
        print(f"\n前 {p}% 子数据集：长度区间 {min_len} ~ {max_len}")

        # 使用长度区间过滤（等同于取前 p%，因为已排序）
        mask = lengths <= max_len
        selected_indices = np.where(mask)[0]

        X_sub_list = [traces_list[i] for i in selected_indices]
        y_sub = y[selected_indices]

        print(f"  提取样本数: {len(y_sub)}, 类别数: {len(np.unique(y_sub))}")

        # 4. 过滤样本数 < min_samples_per_class 的类别
        unique_labels, counts = np.unique(y_sub, return_counts=True)
        valid_labels = unique_labels[counts >= args.min_samples_per_class]
        final_mask = np.isin(y_sub, valid_labels)

        X_filtered_list = [X_sub_list[i] for i in range(len(X_sub_list)) if final_mask[i]]
        y_filtered = y_sub[final_mask]

        # 5. 标签连续重编号
        _, y_new = np.unique(y_filtered, return_inverse=True)

        # 6. 填充到固定长度并转为 numpy array
        X_padded = np.zeros((len(y_new), args.max_len), dtype=int)
        for i, trace in enumerate(X_filtered_list):
            length = min(len(trace), args.max_len)
            X_padded[i, :length] = trace[:length]

        # 7. 保存 NPZ
        # save_name = f"{base_name}_{p}percent.npz"
        save_name = f"{base_name}.npz"
        output_path = os.path.join(args.output_folder, save_name)
        np.savez(output_path, X=X_padded, y=y_new)

        print(f"  过滤后样本数: {len(y_new)}, 剩余类别数: {len(np.unique(y_new))}")
        print(f"  已保存: {output_path}")

    print("\n所有子数据集生成完成！")

if __name__ == "__main__":
    main()