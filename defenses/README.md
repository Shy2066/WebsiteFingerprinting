## 数据集存放位置：
```
/home/shy/Project/dataset/tor_fiber
/home/shy/Project/dataset/tor_starlink
```

## 防御数据集生成

### FRONT 防御

**基本用法：**
```bash
cd defenses/front
python main.py <traces_path> [-c <config>] [-format <suffix>]
```

**参数说明：**
- `<traces_path>`: 原始流量轨迹目录路径
- `-c <config>`: 配置名称，可选值：default, t1, t2, t3, t4, t5（默认：default）
- `-format <suffix>`: 文件后缀

**示例：**
```bash
# 使用默认配置
python main.py ../../data/tor/

cd /home/shy/Project/WebsiteFingerprinting/defenses
python front/main.py /home/shy/Project/dataset/tor_fiber -c t1 --log fiber1
python front/main.py /home/shy/Project/dataset/tor_starlink -c t1 --log starlink
# 使用t1配置
python main.py ../../data/tor/ -c t1

# 为Glue防御的轨迹添加FRONT噪声
python mp_main.py ../results/glued_trace/ -format ".merge"
```

**配置说明（config.ini）：**
- `default`: 9站点×10实例 + 90非监控站点，客户端/服务端各100个虚拟包
- `t1`: 100站点×90实例 + 9000非监控站点，客户端600/服务端1400虚拟包
- `t2`: 同t1，start_padding_time=7
- `t3`: 同t1，start_padding_time=8
- `t4`: 同t1，start_padding_time=9
- `t5`: 同t1，start_padding_time=10

具体调优办法
先用当前参数生成防御后的数据集
用 overhead.py 统计实际 overhead
如果结果：
> 1.24×：降低 client_dummy_pkt_num 和 server_dummy_pkt_num
< 1.24×：提高 client_dummy_pkt_num 和 server_dummy_pkt_num
更精确的估算方法
先计算你的数据集平均真实包数 R：

真实包数 = 非 888、非 999 的包数
然后：

目标假包数 F ≈ 0.24 * R
由于当前实现约为随机 [1, max-1]：
预期假包数 ≈ client_dummy_pkt_num / 2 + server_dummy_pkt_num / 2
因此可以近似按下面方式配置：

client_dummy_pkt_num ≈ 2 * 预期客户端假包数
server_dummy_pkt_num ≈ 2 * 预期服务器假包数



---

### GLUE 防御

**基本用法：**
```bash
cd defenses/glue
python main-base-rate.py <traces_path> -n <num> -m <merged_num> -b <baserate> -noise <True/False> -mode <fix/random>
```

**参数说明：**
- `<traces_path>`: 原始流量轨迹目录路径
- `-n <num>`: 生成的l-trace数量
- `-m <merged_num>`: 每个l-trace合并的轨迹数（l值）
- `-b <baserate>`: 基础比率（默认：10）
- `-noise <True/False>`: 是否添加噪声
- `-mode <fix/random>`: fix=固定长度，random=随机长度

**示例：**
```bash
# 生成4000个长度为2的固定长度l-trace，基础比率为1，添加噪声
python main-base-rate.py ../../data/tor2-5-1/ -n 4000 -m 2 -b 1 -noise True -mode fix

# 批量生成不同长度的l-trace（使用run.py）
python run.py
```

**注意：** 当使用 `-noise True` 时，程序需要非监控站点列表（保存在 `nonsens.txt` 中），用于随机采样作为GLUE噪声轨迹注入到l-trace中。

---

### Tamaraw 防御

**基本用法：**
```bash
cd defenses/tamaraw
python tamaraw.py <traces_path>
```

**参数说明：**
- `<traces_path>`: 原始流量轨迹目录路径

**示例：**
```bash
python tamaraw.py ../../data/tor/
```

**说明：** Tamaraw会自动处理监控站点和非监控站点，生成的防御数据集保存在 `defenses/results/tamaraw_<timestamp>/` 目录中。

---

### WTF-PAD 防御

**基本用法：**
```bash
cd defenses/wtfpad
python main.py <traces_path> [-c <config>]
```

**参数说明：**
- `<traces_path>`: 原始流量轨迹目录路径
- `-c <config>`: 配置名称，可选值：default, normal, normal_rcv, histos, histos_rcv（默认：normal_rcv）

**示例：**
```bash
# 使用默认配置
python main.py ../../data/tor/

# 使用histos配置
python main.py ../../data/tor/ -c histos
```

**配置说明（config.ini）：**
- `normal`: 基于正态分布的发送/接收突发和间隔分布
- `normal_rcv`: 在normal基础上增加接收方向的分布
- `histos`: 基于直方图的分布（需要预生成的直方图文件）
- `histos_rcv`: 在histos基础上增加接收方向的直方图

---

## 数据集后处理

### 计算开销
```bash
cd utils
python overhead.py /home/shy/Project/WebsiteFingerprinting/defenses/results/tor_fiber_front_20260630_103730 -format "" --log fiber_front

python overhead.py /home/shy/Project/WebsiteFingerprinting/defenses/results/tor_starlink_front_20260630_105354 -format "" --log starlink_front
```

### 生成标准化数据集
```bash
cd utils
python norm.py <defended_dataset_path>
```
将±888、±999等噪声标记转换为±1，用于WF攻击评估。

### 清除噪声数据集
```bash
cd utils
python rmnoise.py <defended_dataset_path>
```
从噪声数据集中获取干净数据集（移除±999、±888包）。