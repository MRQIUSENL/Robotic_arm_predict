import time
import numpy as np
import pyvista as pv
from dataclasses import dataclass


def add_3d_axes(plotter, length=3.0):
    """绘制带数轴的 3D 坐标系"""
    # 方向箭头
    origin = np.array([0, 0, 0])
    colors = ["red", "green", "blue"]
    labels = ["X", "Y", "Z"]
    directions = np.eye(3) * length
    for color, d, label in zip(colors, directions, labels):
        plotter.add_mesh(
            pv.Arrow(start=origin, direction=d, tip_length=0.18, tip_radius=0.05, shaft_radius=0.025),
            color=color,
        )
        plotter.add_point_labels(
            [d], [f"{label}"], font_size=11, text_color=color, show_points=False
        )

    # 数轴刻度 + 标尺
    plotter.show_bounds(
        grid=True,
        location="back",
        ticks="both",
        xtitle="X", ytitle="Y", ztitle="Z",
        font_size=10,
        n_xlabels=5, n_ylabels=5, n_zlabels=5,
    )


# ============================================================
# 1. 3D Drawing (PyVista)
# ============================================================
class Draw3D:
    def __init__(self):
        self.points = []
        self.point_actors = []     # 控制点可视化
        self.spline_actor = None
        self.default_radius = 2.5  # 重置用
        self.plotter = pv.Plotter(window_size=[900, 700])
        self.plotter.add_title(
            "Click sphere to draw | Buttons: Undo / Clear / Reset | Slider: Radius",
            font_size=9,
        )
        self.plotter.set_background("white")
        add_3d_axes(self.plotter)

        # 半透明球体作为 3D 拾取面
        self.sphere = pv.Sphere(radius=self.default_radius)
        self.sphere_actor = self.plotter.add_mesh(
            self.sphere,
            color="lightgray",
            opacity=0.08,
            show_edges=True,
            edge_color="gray",
        )

        # ---- 控制按钮 ----
        btn_y = 55
        btn_size = 28
        btn_gap = 40
        btn_x = 10

        # Undo
        self.plotter.add_checkbox_button_widget(
            callback=lambda s: s and self._undo(),
            value=False,
            position=(btn_x, btn_y),
            size=btn_size,
            color_on="orange",
            color_off="lightgray",
            background_color="white",
        )
        btn_x += btn_gap

        # Clear
        self.plotter.add_checkbox_button_widget(
            callback=lambda s: s and self._clear_all(),
            value=False,
            position=(btn_x, btn_y),
            size=btn_size,
            color_on="red",
            color_off="lightgray",
            background_color="white",
        )
        btn_x += btn_gap

        # Reset
        self.plotter.add_checkbox_button_widget(
            callback=lambda s: s and self._reset(),
            value=False,
            position=(btn_x, btn_y),
            size=btn_size,
            color_on="green",
            color_off="lightgray",
            background_color="white",
        )

        # 按钮标签
        for lbl_x, lbl_text in [(15, "Undo"), (55, "Clear"), (95, "Reset")]:
            self.plotter.add_text(
                lbl_text, position=(lbl_x, btn_y + btn_size + 2),
                font_size=8, color="black",
            )

        self._add_radius_slider()

        self.plotter.enable_point_picking(
            callback=self.on_click, show_message=True, left_clicking=True
        )
        self.plotter.show()

    def _add_radius_slider(self):
        """添加/重置半径滑块"""
        self.plotter.clear_slider_widgets()
        self.plotter.add_slider_widget(
            callback=lambda v: self._on_slider(v),
            rng=[0.3, 5.0],
            value=self.default_radius,
            title="Radius",
            pointa=(0.72, 0.03),
            pointb=(0.92, 0.03),
            fmt="%.2f",
        )

    def _on_slider(self, value):
        self.sphere = pv.Sphere(radius=value)
        self.sphere_actor.mapper.dataset = self.sphere
        b = value * 1.05
        self.plotter.show_bounds(
            bounds=[-b, b, -b, b, -b, b],
            grid=True, location="back", ticks="both",
            font_size=10, n_xlabels=5, n_ylabels=5, n_zlabels=5,
        )
        self.plotter.render()

    def _undo(self):
        """撤回上一个控制点"""
        if not self.points:
            return
        self.points.pop()
        if self.point_actors:
            self.plotter.remove_actor(self.point_actors.pop())
        self._refresh_spline()

    def _clear_all(self):
        """清除所有控制点"""
        self.points.clear()
        for a in self.point_actors:
            self.plotter.remove_actor(a)
        self.point_actors.clear()
        if self.spline_actor is not None:
            self.plotter.remove_actor(self.spline_actor)
            self.spline_actor = None
        self.plotter.add_title(
            "All cleared | Click sphere to draw new path",
            font_size=9,
        )
        self.plotter.render()

    def _reset(self):
        """重置球体和滑块到默认大小"""
        self.sphere = pv.Sphere(radius=self.default_radius)
        self.sphere_actor.mapper.dataset = self.sphere
        b = self.default_radius * 1.05
        self.plotter.show_bounds(
            bounds=[-b, b, -b, b, -b, b],
            grid=True, location="back", ticks="both",
            font_size=10, n_xlabels=5, n_ylabels=5, n_zlabels=5,
        )
        self._add_radius_slider()
        self.plotter.render()

    def _refresh_spline(self):
        """更新样条预览"""
        if len(self.points) < 2:
            if self.spline_actor is not None:
                self.plotter.remove_actor(self.spline_actor)
                self.spline_actor = None
            self.plotter.render()
            return
        raw = np.vstack(self.points)
        spline_pts = self._catmull_rom_spline(raw, samples_per_segment=20)
        spline = pv.Spline(spline_pts, len(spline_pts) * 2)
        if self.spline_actor is None:
            self.spline_actor = self.plotter.add_mesh(
                spline, color="red", line_width=3, opacity=0.7
            )
        else:
            self.spline_actor.mapper.dataset = spline
        self.plotter.add_title(
            f"Points: {len(self.points)} | 🟠Undo  🔴Clear  🟢Reset | Close when done",
            font_size=9,
        )
        self.plotter.render()

    def on_click(self, point):
        pt = np.asarray(point).reshape(1, 3)
        self.points.append(pt)
        actor = self.plotter.add_points(
            pv.PolyData(pt), color="blue", point_size=8
        )
        self.point_actors.append(actor)
        self._refresh_spline()

    def get_path(self):
        if len(self.points) < 2:
            return None
        raw = np.vstack(self.points)
        return self._catmull_rom_spline(raw, samples_per_segment=20)

    @staticmethod
    def _catmull_rom_spline(control_pts, samples_per_segment=20):
        """Catmull-Rom 样条：通过所有控制点的平滑 3D 曲线"""
        pts = np.asarray(control_pts)
        n = len(pts)
        if n < 3:
            return pts  # 太少点就直接连

        # 端点镜像以处理首尾
        p0 = pts[0] - (pts[1] - pts[0])
        pn = pts[-1] - (pts[-2] - pts[-1])
        padded = np.vstack([p0, pts, pn])

        samples = []
        for i in range(1, len(padded) - 2):
            p0, p1, p2, p3 = padded[i - 1], padded[i], padded[i + 1], padded[i + 2]
            for t in np.linspace(0, 1, samples_per_segment, endpoint=False):
                t2, t3 = t * t, t * t * t
                pt = 0.5 * (
                    (2 * p1)
                    + (-p0 + p2) * t
                    + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                    + (-p0 + 3 * p1 - 3 * p2 + p3) * t3
                )
                samples.append(pt)
        samples.append(pts[-1])  # 最后一个点
        return np.array(samples)


# ============================================================
# 2. 3D Robotic Arm
# ============================================================
@dataclass
class Arm3D:
    lengths: np.ndarray

    @property
    def n(self):
        return len(self.lengths)

    def forward(self, pitch, yaw):
        joints = [[0.0, 0.0, 0.0]]
        x = y = z = 0.0
        for i in range(len(self.lengths)):
            l = self.lengths[i]
            x += l * np.cos(pitch[i]) * np.cos(yaw[i])
            y += l * np.cos(pitch[i]) * np.sin(yaw[i])
            z += l * np.sin(pitch[i])
            joints.append([x, y, z])
        return np.array(joints)

    def inverse(self, target, prev_pitch, prev_yaw):
        """FABRIK 逆运动学：几何迭代法，快速稳健"""
        n = len(self.lengths)
        lengths = self.lengths
        target = np.asarray(target)

        # 用前一步角度初始化关节位置
        joints = self.forward(prev_pitch, prev_yaw).astype(float)

        for _ in range(10):
            # 反向传递：从末端拉到目标
            joints[-1] = target
            for i in range(n - 1, -1, -1):
                d = joints[i + 1] - joints[i]
                dist = np.linalg.norm(d)
                if dist > 0:
                    joints[i] = joints[i + 1] - d * (lengths[i] / dist)

            # 正向传递：根部固定在原点
            joints[0] = [0, 0, 0]
            for i in range(n):
                d = joints[i + 1] - joints[i]
                dist = np.linalg.norm(d)
                if dist > 0:
                    joints[i + 1] = joints[i] + d * (lengths[i] / dist)

            # 检查收敛
            if np.linalg.norm(joints[-1] - target) < 1e-6:
                break

        # 关节位置 → pitch/yaw 角度
        pitch = np.zeros(n)
        yaw = np.zeros(n)
        for i in range(n):
            d = joints[i + 1] - joints[i]
            pitch[i] = np.arcsin(np.clip(d[2] / lengths[i], -1.0, 1.0))
            yaw[i] = np.arctan2(d[1], d[0])

        # 角度解包：防止从 π 跳到 -π 导致转圈
        for i in range(n):
            while pitch[i] - prev_pitch[i] > np.pi:
                pitch[i] -= 2 * np.pi
            while pitch[i] - prev_pitch[i] < -np.pi:
                pitch[i] += 2 * np.pi
            while yaw[i] - prev_yaw[i] > np.pi:
                yaw[i] -= 2 * np.pi
            while yaw[i] - prev_yaw[i] < -np.pi:
                yaw[i] += 2 * np.pi

        return pitch, yaw


# ============================================================
# 3. Link Optimizer
# ============================================================
class LinkOptimizer:
    def __init__(self, path, max_links=5):
        self.path = path
        self.max_links = max_links

    def optimize(self):
        results = {}
        for n in range(1, self.max_links + 1):
            best_len = None
            best_err = np.inf
            for _ in range(12):
                lengths = np.random.uniform(0.2, 1.5, n)
                lengths *= 2.5 / np.sum(lengths)
                arm = Arm3D(lengths)
                err = self._eval_lengths(arm)
                if err < best_err:
                    best_err = err
                    best_len = lengths

            arm = Arm3D(best_len)
            res = self._eval_arm(arm, n)
            res["lengths"] = best_len
            results[n] = res
            print(
                f"  {n}-link | "
                f"Error={res['mean_error']:.4f} | "
                f"Smooth={res['smoothness']:.4f} | "
                f"Score={res['score']:.3f}"
            )

        best_n = min(results, key=lambda k: results[k]["score"])
        # 存储对应的 arm 实例和 path
        for n in results:
            results[n]["arm"] = Arm3D(results[n]["lengths"])
        results["_best"] = best_n
        return results

    def _eval_lengths(self, arm):
        err = 0.0
        idx = np.linspace(0, len(self.path) - 1, 30, dtype=int)
        p = np.zeros(arm.n)
        y = np.zeros(arm.n)
        for i in idx:
            p, y = arm.inverse(self.path[i], p, y)
            err += np.linalg.norm(arm.forward(p, y)[-1] - self.path[i])
        return err / len(idx)

    def _eval_arm(self, arm, n):
        errors = []
        angles = []
        p = np.zeros(arm.n)
        y = np.zeros(arm.n)
        for pt in self.path:
            p, y = arm.inverse(pt, p, y)
            arm.forward(p, y)
            errors.append(np.linalg.norm(arm.forward(p, y)[-1] - pt))
            angles.append(np.concatenate([p, y]))

        angles = np.array(angles)
        smooth = np.mean(np.abs(np.diff(angles, axis=0))) if len(angles) > 2 else 0.0
        mean_err = np.mean(errors)
        cov = np.mean(np.array(errors) < 0.1)
        score = mean_err * 10 + smooth * 3 + (1 - cov) * 2 + n * 0.15

        return {
            "mean_error": mean_err,
            "smoothness": smooth,
            "coverage": cov,
            "score": score,
            "angles": angles,
        }


# ============================================================
# 4. 3D Animation (PyVista)
# ============================================================
class Arm3DAnimation:
    def __init__(self, arm, path, angles):
        self.arm = arm
        self.path = path
        self.angles = angles

        self.plotter = pv.Plotter(window_size=[1000, 800])
        self.plotter.add_title("3D Robotic Arm Simulation")
        self.plotter.set_background("white")
        add_3d_axes(self.plotter)

        # Target path
        self.plotter.add_mesh(
            pv.Spline(self.path, 200),
            color="green",
            line_width=3,
            opacity=0.5,
        )

        self.joints = None
        self.lines = []
        self.trail_points = []  # 末端轨迹点
        self.trail_actor = None

    def run(self, arm_label=""):
        n = self.arm.n
        sub_steps = 20

        self.plotter.add_title(arm_label, font_size=10)
        self._skip = False

        self._anim_idx = 0
        self._anim_sub = 0
        self._anim_n = n
        self._anim_sub_steps = sub_steps
        self._anim_prev = self.angles[0]
        self._anim_next = self.angles[1 % len(self.angles)]

        def on_key(caller, event):
            key = caller.GetKeySym().lower() if hasattr(caller, 'GetKeySym') else ''
            if key in ('space', 'right', 'n'):
                self._skip = True

        def on_timer(caller, event):
            self._tick()

        self.plotter.iren.add_observer("KeyPressEvent", on_key)
        self.plotter.iren.add_observer("TimerEvent", on_timer)
        self.plotter.iren.create_timer(20)

        try:
            self.plotter.show()
        except Exception:
            pass  # 窗口已关闭

    def _tick(self):
        """定时器回调：计算一帧并渲染"""
        if self._skip:
            try:
                self.plotter.close()
            except Exception:
                pass
            return

        n = self._anim_n
        t = self._anim_sub / self._anim_sub_steps
        current = self._anim_prev + (self._anim_next - self._anim_prev) * t

        # 正运动学
        p, y = current[:n], current[n:]
        joints = self.arm.forward(p, y)
        self._update_actors(joints, n)

        # 末端轨迹
        self.trail_points.append(joints[-1].copy())
        if len(self.trail_points) > 800:
            self.trail_points = self.trail_points[-800:]
        self._update_trail()

        self.plotter.render()

        # 推进帧
        self._anim_sub += 1
        if self._anim_sub >= self._anim_sub_steps:
            self._anim_sub = 0
            self._anim_idx += 1
            if self._anim_idx >= len(self.angles):
                self._anim_idx = 0
            self._anim_prev = self.angles[self._anim_idx]
            self._anim_next = self.angles[
                (self._anim_idx + 1) % len(self.angles)
            ]

    def _update_trail(self):
        """更新末端轨迹线"""
        if len(self.trail_points) < 2:
            return
        trail = pv.Spline(np.array(self.trail_points), len(self.trail_points) * 2)
        if self.trail_actor is None:
            self.trail_actor = self.plotter.add_mesh(
                trail, color="orange", line_width=2, opacity=0.7
            )
        else:
            self.trail_actor.mapper.dataset = trail

    def _update_actors(self, joints, n):
        """创建或更新关节球和连杆线"""
        if self.joints is None:
            self.joints = [
                self.plotter.add_mesh(
                    pv.PolyData(j.reshape(1, 3)),
                    color="red",
                    point_size=10,
                )
                for j in joints
            ]
            for k in range(n):
                self.lines.append(
                    self.plotter.add_mesh(
                        pv.Line(joints[k], joints[k + 1]),
                        color="blue",
                        line_width=4,
                    )
                )
        else:
            for k in range(n + 1):
                self.joints[k].mapper.dataset = pv.PolyData(
                    joints[k].reshape(1, 3)
                )
            for k in range(n):
                self.lines[k].mapper.dataset = pv.Line(
                    joints[k], joints[k + 1]
                )


# ============================================================
# 5. Main
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  3D Robotic Arm Auto-Optimization System")
    print("=" * 60)

    # Draw
    drawer = Draw3D()
    path = drawer.get_path()

    if path is None or len(path) < 3:
        print("Using default 3D trajectory.")
        t = np.linspace(0, 2 * np.pi, 400)
        path = np.column_stack(
            [
                np.cos(2 * t) * 1.5,
                np.sin(3 * t) * 1.5,
                np.sin(t) * 1.2,
            ]
        )

    # Normalize
    path -= np.mean(path, axis=0)
    path /= np.max(np.linalg.norm(path, axis=1)) * (1 / 2.0)

    # Optimize
    opt = LinkOptimizer(path)
    results = opt.optimize()
    best_n = results["_best"]

    link_nums = sorted([k for k in results if isinstance(k, int)])

    print(f"\nBest: {best_n}-link arm (lowest score)")
    for n in link_nums:
        r = results[n]
        print(
            f"  [{n}] {n}-link | "
            f"Error={r['mean_error']:.4f} | "
            f"Smooth={r['smoothness']:.4f} | "
            f"Cover={r['coverage']:.1%} | "
            f"Score={r['score']:.3f}"
            f"{'  <-- BEST' if n == best_n else ''}"
        )

    # 用户选择
    print("\nEnter number to animate (e.g. 3), or 'all' to cycle:")
    choice = input("> ").strip().lower()

    if choice == "all":
        to_animate = [best_n] + [n for n in link_nums if n != best_n]
    elif choice.isdigit() and int(choice) in results:
        to_animate = [int(choice)]
    else:
        print(f"Invalid choice, showing best ({best_n}-link)")
        to_animate = [best_n]

    for i, n in enumerate(to_animate):
        r = results[n]
        label = f"{n}-link arm ({i+1}/{len(to_animate)})"
        if n == best_n:
            label += " [BEST]"
        label += " | Space=skip, X=next"
        print(f"\n▶ {label}")
        anim = Arm3DAnimation(r["arm"], path, r["angles"])
        anim.run(arm_label=label)