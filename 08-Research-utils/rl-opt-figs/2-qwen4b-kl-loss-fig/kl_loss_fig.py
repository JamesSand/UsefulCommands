import re
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

# 假设第1列是 step，后面两列就是两条 KL 曲线（与你这个 csv 一致）
step = df.iloc[:, 0]
y_cols = df.columns[1:3]

def nice_label(col_name: str) -> str:
    # # 从列名里提取 constraint 的值，做成更短的图例（不想要可直接 return col_name）
    # m = re.search(r"constraint-([0-9.eE+-]+)", col_name)
    # return f"constraint={m.group(1)}" if m else col_name
    
    print(col_name)
    
    if "trace-constraint-0.0" in col_name:
        # adamW case
        return "Qwen3-4B-AdamW"
    else:
        # this should be 1e-4, should be trace constraint case
        return "Qwen3-4B-AdamW-w-Trace"
    
    
    

plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams.update({
    "figure.dpi": 120,
    "savefig.dpi": 300,
    "font.size": 12,
    "axes.labelsize": 13,
    "legend.fontsize": 13,
    "lines.linewidth": 2.0,
    "axes.spines.top": True,
    "axes.spines.right": True,
    "axes.spines.bottom": True,
    "axes.spines.left": True,
    "pdf.fonttype": 42,   # 避免 PDF 里 Type3 字体，paper 更友好
    "ps.fonttype": 42,
})

fig, ax = plt.subplots(figsize=(6.5, 3.8))

for col in y_cols:
    ax.plot(step, df[col], label=nice_label(col))

ax.set_title("Qwen3 4B: KL loss during training")
ax.set_xlabel("Training step")
ax.set_ylabel("KL loss")
ax.set_xlim(step.min(), step.max())
ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))  # y 轴科学计数法
ax.grid(True, linestyle='--', alpha=0.6)  # 虚线网格

# 设置外边框为黑色实线
for spine in ax.spines.values():
    spine.set_edgecolor('black')
    spine.set_linewidth(1)
    spine.set_linestyle('-')

ax.legend(frameon=True, edgecolor='lightgray', fancybox=False)

fig.tight_layout()
fig.savefig("kl_loss.png")
fig.savefig("kl_loss.pdf")
plt.show()




