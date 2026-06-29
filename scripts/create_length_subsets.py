import numpy as np

"""
将npz数据集按长度进行分类并保存为NPZ文件
假设原始NPZ文件包含 'X' (shape: (样本数, 10000)) 和 'y' (shape: (样本数,)) 两个数组
每个样本的有效长度定义为非零元素的最后一个索引 + 1
每个子集按有效长度从小到大排序，取前10%、20%、30%、40%、50%的样本，过滤掉类别样本数少于100的类别，并重编号标签后保存为新的NPZ文件 
"""
SOURCE_DATA_FOLDER = '/home/shy/Project/Website-Fingerprinting-Library/datasets/CW.npz' 

# 加载数据
data = np.load(SOURCE_DATA_FOLDER)  # 假设你的文件是这个；如果不是，改成你的文件名
X = data['X']             # shape: (样本数, 10000)
y = data['y']             # shape: (样本数,)
N = X.shape[0]

print(f"原始样本数: {N}")
print(f"原始类别数: {len(np.unique(y))}")

# 步骤1: 计算每个序列的有效长度
lengths = np.zeros(N, dtype=int)
for i in range(N):
    trace = X[i]
    nonzero_indices = np.where(trace != 0)[0]
    if len(nonzero_indices) > 0:
        lengths[i] = nonzero_indices[-1] + 1
    else:
        lengths[i] = 0
    if i % 1000 == 0:        # 进度打印，调整成你的N大小
        print(f"处理进度: {i}/{N}")

# 打印长度统计，让你检查合理性
print(f"最小长度: {lengths.min()}, 最大: {lengths.max()}, 平均: {lengths.mean():.2f}")

# 建立记录表
table = np.column_stack([np.arange(N), lengths])

# 步骤2: 按长度从小到大排序
sorted_idx = np.argsort(lengths)
lengths_sorted = lengths[sorted_idx]

# 步骤3-5: 循环每个百分比
# percentiles = [10, 20, 30, 40, 50]
percentiles = [100]
for p in percentiles:
    n = int(N * p / 100)
    min_len = lengths_sorted[0]
    max_len = lengths_sorted[n-1]
    print(f"前{p}% 的有效长度区间: {min_len} - {max_len}")
    
    # 步骤4: 依据区间提取子集
    mask = (lengths >= min_len) & (lengths <= max_len)
    X_sub = X[mask]
    y_sub = y[mask]
    
    # 临时统计，看看提取了多少
    print(f"提取后样本数: {len(y_sub)}, 类别数: {len(np.unique(y_sub))}")
    
    # 步骤5: 过滤<100条的类，并重编号标签
    unique, counts = np.unique(y_sub, return_counts=True)
    # valid_classes = unique[counts >= 100]
    valid_classes = unique
    mask_valid = np.isin(y_sub, valid_classes)
    
    X_final = X_sub[mask_valid]
    y_final_old = y_sub[mask_valid]
    y_final = np.unique(y_final_old, return_inverse=True)[1]
    
    # 保存最终NPZ
    save_name = f'CW_{p}percent.npz'
    np.savez(save_name, X=X_final, y=y_final)
    
    # 最终统计
    print(f"{save_name} 已保存！样本数: {len(y_final)}, 类别数: {len(np.unique(y_final))}")
    print("=" * 50)

print("全部完成！检查你的新NPZ文件吧。")