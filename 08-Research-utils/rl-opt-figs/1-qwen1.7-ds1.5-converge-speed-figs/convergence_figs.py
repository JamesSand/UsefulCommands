
import pandas as pd, matplotlib.pyplot as plt

bias = 0

plt.rcParams.update({
    "font.size": 12 + bias,          # 全局默认字体
    "axes.titlesize": 16 + bias,     # title
    "axes.labelsize": 15 + bias,     # x/y label
    "xtick.labelsize": 13 + bias,    # x tick
    "ytick.labelsize": 13 + bias,    # y tick
    "legend.fontsize": 13 + bias,    # legend
})

raw = pd.read_excel("data.xlsx", sheet_name=0, header=None)
S = lambda a,b,h,c0,c1: raw.iloc[a:b,c0:c1].copy().set_axis(raw.iloc[h,c0:c1], axis=1).astype(float)

qA, dsA = S(3,14,2,1,8),  S(3,14,2,9,16)     # AdamW
qM, dsM = S(18,29,17,1,8), S(18,29,17,9,16)  # ISO (ours)

def P(A, M, title, out):
    y = A["avg"].max()
    xa = A.loc[A["avg"].idxmax(), "step"]
    xm = M.loc[M["avg"] >= y, "step"].min()
    fig, ax = plt.subplots(figsize=(7.2, 4.6), dpi=300)
    ax.plot(A.step, A.avg, "o-", lw=2, label="AdamW")
    ax.plot(M.step, M.avg, "s-", lw=2, label="ISO (ours)")
    ax.axhline(y, ls="--", lw=1); ax.scatter([xa, xm], [y, y], zorder=5)
    ax.annotate("", xy=(xm, y), xytext=(xa, y), arrowprops=dict(arrowstyle="->", lw=2))  # right -> left

    saved = xa - xm
    saved_ratio = saved / xa * 100

    ax.text((xa+xm)/2, y + (ax.get_ylim()[1]-ax.get_ylim()[0])*0.04, f"Training efficiency ({saved_ratio:.1f}%  fewer steps)", ha="center")

    ax.text(0.02, 0.96, f"Target (AdamW best @0–200): {y:.3f}\nAdamW: {xa:.0f} | ISO: {xm:.0f}\nSaved: {saved:.0f} ({saved_ratio:.1f}% fewer)",
            transform=ax.transAxes, va="top", ha="left", 
            bbox=dict(
            boxstyle="round,pad=0.35",
            facecolor="#EAF2FB",   # very light blue
            edgecolor="#A9C4E3",   # soft blue-gray border
            linewidth=0.9,
            alpha=0.3,
        ))
    ax.set(title=title, xlabel="Training steps", ylabel="Average accuracy (avg)")
    ax.grid(True, ls=":", lw=0.9, alpha=0.75)
    ax.legend(frameon=False, loc="lower right")
    fig.tight_layout()

    # save as pdf
    fig.savefig(out.replace(".png", ".pdf"), bbox_inches="tight")

    # # save as png
    # fig.savefig(out, bbox_inches="tight")

    plt.close(fig)

P(qA,  qM,  "Qwen-1.7B: Convergence (Avg accuracy vs Steps)", "qwen1_7b_svdmuon_vs_adam.png")
P(dsA, dsM, "DS-1.5B: Convergence (Avg accuracy vs Steps)",   "ds1_5b_svdmuon_vs_adam.png")



