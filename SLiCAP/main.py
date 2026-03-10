import tkinter as tk
from tkinter import ttk, messagebox
import SLiCAP as sl
import os
import threading
import sympy as sp
import numpy as np

# ================= 1. 基础参数定义 =================
# 这些参数将与网表中的 {占位符} 对应并被注入
CIRCUIT_PARAMS = {
    'R_s': 50,
    'R_b1': 47e3,
    'R_b2': 10e3,
    'R_c': 2200,
    'R_e': 100,
    'R_L': 10e3,
    'V_cc': 12,  # V_cc 仅用于在Python中计算直流工作点
}
CAP_PARAMS = {
    'C_in': 10e-6,
    'C_out': 10e-6,
}

PROJECT_NAME = 'SLiCAP_Analysis'
# 代码将直接读取位于 'cir' 文件夹下的这个文件
NETLIST_NAME = 'direct_ce.cir'


# ================= 2. 核心分析逻辑 =================
class SlicapAnalyzer:
    def __init__(self):
        self.gain_val = "N/A"
        self.zin_val = "N/A"
        self.small_signal_params = {}

    def _calc_bias_point(self):
        """
        在 Python 端估算 DC 工作点，为混合π模型提供 gm 和 rpi 参数。
        """
        p = CIRCUIT_PARAMS
        # 基极电压估算 (戴维南等效)
        vb = p['V_cc'] * p['R_b2'] / (p['R_b1'] + p['R_b2'])
        # 发射极电压 (Vbe 压降为 0.7V)
        ve = vb - 0.7
        if ve <= 0:
            raise ValueError("偏置点错误: 发射极电压不是正数。请检查偏置电阻。")
        # 发射极电流
        ie = ve / p['R_e']
        # 跨导 gm (热电压 Vt ≈ 26mV)
        gm = ie / 0.026
        # 输入电阻 rpi (假设 beta = 200)
        rpi = 200 / gm

        # 将计算出的参数存入字典，准备注入网表
        self.small_signal_params = {
            'g_m': gm,
            'r_pi': rpi,
            'r_o': 100e3  # 假设一个典型的厄利电阻 ro = 100k
        }
        print(f"DC Est: Vb={vb:.2f}V, Ie={ie * 1000:.2f}mA -> gm={gm:.3f}S, rpi={rpi:.1f}Ω")

    def run(self):
        """
        执行完整的 SLiCAP 分析流程
        """
        try:
            # 初始化 SLiCAP 项目
            sl.initProject(PROJECT_NAME)

            # 1. 检查用户提供的网表文件是否存在
            netlist_path = os.path.join('cir', NETLIST_NAME)
            if not os.path.exists(netlist_path):
                raise FileNotFoundError(f"网表文件未找到: {netlist_path}\n请确认文件已按要求创建。")

            # 2. 计算小信号参数 (gm, rpi)，为网表中的占位符准备数值
            self._calc_bias_point()

            # 3. 创建并配置 SLiCAP 分析指令
            instruction = sl.instruction()
            instruction.setCircuit(NETLIST_NAME)  # 直接加载用户的文件

            # 将所有参数（电路参数、电容、计算出的小信号参数）合并
            all_params = {**CIRCUIT_PARAMS, **self.small_signal_params, **CAP_PARAMS}
            for key, val in all_params.items():
                instruction.defPar(key, val)

            # --- 增益分析 ---
            instruction.setSource('V1')
            instruction.setDetector('V_c')  # 探测集电极电压
            instruction.setGainType('gain')
            instruction.setDataType('laplace')
            res_gain = sl.doLaplace(instruction)

            # 检查仿真是否成功返回表达式
            if not hasattr(res_gain, 'laplace') or isinstance(res_gain.laplace, list):
                err_info = str(getattr(res_gain, 'laplace', "未知SLiCAP错误"))
                raise RuntimeError(f"SLiCAP 仿真失败. 信息: {err_info}")

            # --- 数值计算 ---
            expr = res_gain.laplace.subs(all_params)
            s_val = 1j * 2 * np.pi * 1000  # 频率设为 1kHz
            final_val = expr.subs({'s': s_val})

            abs_val = float(abs(final_val))
            db_val = 20 * np.log10(abs_val) if abs_val > 0 else -999
            self.gain_val = f"{abs_val:.2f} ({db_val:.1f} dB)"

            # --- 输入阻抗分析 ---
            instruction.setDetector('V_in')  # 探测输入电压
            instruction.setGainType('vi')  # 计算 V_in / I(V1)
            res_zin = sl.doLaplace(instruction)

            if hasattr(res_zin, 'laplace') and not isinstance(res_zin.laplace, list):
                expr_z = res_zin.laplace.subs(all_params)
                val_z = expr_z.subs({'s': s_val})
                self.zin_val = f"{float(abs(val_z)) / 1e3:.2f} kΩ"
            else:
                self.zin_val = "计算错误"

            return True, "分析完成"

        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f"出错: {str(e)}"


# ================= 3. GUI 界面 (无变化) =================
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("SLiCAP Amplifier Tool")
        self.root.geometry("450x300")

        frame = ttk.Frame(root, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="CE Amplifier Analyzer", font=("Arial", 14, "bold")).pack(pady=10)

        self.v_gain = tk.StringVar(value="---")
        self.v_zin = tk.StringVar(value="---")
        self.v_status = tk.StringVar(value="Ready")

        self._row(frame, "Voltage Gain (@1kHz):", self.v_gain)
        self._row(frame, "Input Impedance:", self.v_zin)

        ttk.Label(frame, textvariable=self.v_status, foreground="#555").pack(pady=15)
        ttk.Button(frame, text="Run Analysis", command=self.start).pack()

        self.analyzer = SlicapAnalyzer()

    def _row(self, parent, label, var):
        f = ttk.Frame(parent)
        f.pack(fill=tk.X, pady=5)
        ttk.Label(f, text=label, width=20).pack(side=tk.LEFT)
        ttk.Label(f, textvariable=var, foreground="blue", font=("Arial", 10, "bold")).pack(side=tk.LEFT)

    def start(self):
        self.v_status.set("Analyzing...")
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        ok, msg = self.analyzer.run()
        self.root.after(0, lambda: self._done(ok, msg))

    def _done(self, ok, msg):
        self.v_status.set(msg)
        if ok:
            self.v_gain.set(self.analyzer.gain_val)
            self.v_zin.set(self.analyzer.zin_val)
        else:
            messagebox.showerror("Error", msg)


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()