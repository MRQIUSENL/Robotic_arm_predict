# 3D Robotic Arm Auto-Optimization System

在 3D 空间中自由绘制目标路径，自动优化机械臂的连杆长度，使用 FABRIK 逆运动学实现高精度轨迹跟踪。

## 功能

1. **3D 自由绘制** — 可调半径球体上点击放置控制点，Catmull-Rom 样条实时生成平滑 3D 曲线
2. **自动臂优化** — 搜索 1-5 连杆臂的最佳臂长配比，基于误差/平滑度/覆盖率评分
3. **FABRIK 逆运动学** — 几何迭代 IK，快速稳健，带角度解包防转圈
4. **多连杆对比** — 优化后显示所有连杆数评分，用户可选择单个或浏览全部动画
5. **实时动画** — VTK 定时器驱动，末端轨迹可视化，支持 Space 跳过

## 运行

```bash
pip install numpy pyvista
python robotic_arm_3D.py
```

## 交互

### 绘图窗口

| 操作 | 方式 |
|------|------|
| 放置控制点 | 左键点击球体表面 |
| 旋转视角 | 右键拖拽 |
| 缩放 | 滚轮 |
| 调整球半径 | 右下角 Radius 滑块 |
| 撤回上一个点 | 🟠 Undo 按钮 |
| 清除所有点 | 🔴 Clear 按钮 |
| 重置球大小 | 🟢 Reset 按钮 |
| 完成绘图 | 关闭窗口 |

- 🔵 蓝色球 = 控制点 · 🔴 红色曲线 = Catmull-Rom 样条实时预览
- 灰色半透明球体 + 数轴网格随半径自适应缩放
- 少于 3 个控制点将使用默认 3D 轨迹

### 终端选择

```
Enter number to animate (e.g. 3), or 'all' to cycle:
```

- 输入数字 → 只看指定连杆数
- 输入 `all` → 先播最优，再依次播其余
- 直接回车 → 播放最优解

### 动画窗口

| 操作 | 方式 |
|------|------|
| 旋转/缩放/平移 | 鼠标交互 |
| 跳过当前动画 | Space 键 |
| 退出 | 窗口 X 按钮 |

- 🟢 绿色曲线 = 目标路径
- 🔵 蓝色线 = 连杆 · 🔴 红色球 = 关节
- 🟠 橙色轨迹 = 末端执行器实际路径
- 标题栏显示当前连杆数、进度、操作提示

## 技术栈

| 组件 | 方案 |
|------|------|
| 3D 渲染 | PyVista / VTK |
| 逆运动学 | FABRIK（前向后向迭代） |
| 路径平滑 | Catmull-Rom 样条插值 |
| 臂优化 | 随机搜索 + 加权评分函数 |
| 动画 | VTK 定时器 + 交互事件循环 |

## 依赖

- Python ≥ 3.9
- numpy
- pyvista ≥ 0.46

## 结果

### Terminal

<img width="848" height="611" alt="c40f13f5e27a168d6d0b539d1044b53e" src="https://github.com/user-attachments/assets/bd20d0d6-0971-475d-b32b-ed38e61b8c03" />

### Print

<img width="899" height="724" alt="bc287b24a4171e3becf3fabe39a22cb7" src="https://github.com/user-attachments/assets/607b858a-ffe6-4b2a-867f-7eadb3c3f196" />

### Result

<img width="1009" height="832" alt="061658ade4cd99475d2a7a6cdfc4117c" src="https://github.com/user-attachments/assets/c88cdad3-d493-486e-b254-e8fe2302d782" />

<img width="1009" height="832" alt="7acd4b0ba319b02aa852fe879991169a" src="https://github.com/user-attachments/assets/0c18ac9a-9973-42f3-be86-6d268fda3e36" />

<img width="1009" height="812" alt="6602031fb0b07784b79770823e71a00c" src="https://github.com/user-attachments/assets/4c7c44dd-e3f5-4055-973c-01d45883f708" />
