"""t-SNE 高维数据可视化（Python 最小可运行模板）

用途：仅用于高维数据二维可视化，不用于解释簇间距离；输出嵌入坐标与 KL 散度。
接口：solve(X, perplexity) -> (嵌入坐标, KL 散度)；运行：python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_common" / "python"))
from mmlib import demo, report, save_fig, save_table, set_style  # noqa: E402


def build_demo() -> dict:
    rng = np.random.default_rng(42)
    X = np.vstack([rng.normal(loc=np.full(8, shift), scale=0.8, size=(80, 8))
                   for shift in (0.0, 2.0, 4.0)])
    return {"X": X, "labels": np.repeat([0, 1, 2], 80), "perplexity": 30}


def solve(X, perplexity: int = 30, seed: int = 42):
    X = StandardScaler().fit_transform(np.asarray(X, float))
    model = TSNE(n_components=2, perplexity=perplexity, init="pca", learning_rate="auto",
                 max_iter=1000, random_state=seed)
    embedding = model.fit_transform(X)
    return embedding, float(model.kl_divergence_)


if __name__ == "__main__":
    data = demo(__file__, build_demo)
    embedding, kl = solve(data["X"], int(data["perplexity"]))
    report("t-SNE", 困惑度=int(data["perplexity"]), KL散度=round(kl, 4), 样本数=len(embedding))
    save_table(__file__, "嵌入坐标", {"样本": np.arange(1, len(embedding) + 1),
                                      "T1": np.round(embedding[:, 0], 6),
                                      "T2": np.round(embedding[:, 1], 6),
                                      "类别": data["labels"]})
    plt = set_style()
    fig, ax = plt.subplots()
    for label, color in zip(sorted(set(data["labels"])), ["#0072B2", "#D55E00", "#009E73"]):
        mask = np.asarray(data["labels"]) == label
        ax.scatter(embedding[mask, 0], embedding[mask, 1], s=16, color=color, label=f"类别 {label + 1}")
    ax.set_xlabel("t-SNE 维度 1")
    ax.set_ylabel("t-SNE 维度 2")
    ax.set_title(f"困惑度={data['perplexity']}，KL={kl:.3f}")
    ax.legend()
    save_fig(__file__, fig, "tsne")
