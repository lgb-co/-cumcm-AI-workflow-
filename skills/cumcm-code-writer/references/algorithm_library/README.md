# 算法参考库

> 面向数模代码编写：命中的每一个算法都能在这里找到**最小可运行实现**（Python + MATLAB）、演示数据与元数据，用来对齐接口、参数写法与常见坑。
> 数量：71 个算法 / 142 个语言模板，覆盖 10 大类。

## 目录结构

```text
algorithm_library/
├── registry.csv          # 元数据唯一来源（id、中文名、题型、成立条件、常见坑、来源、许可）
├── manifest.csv          # 构建产物：模板路径、扫描到的依赖、烟测状态
├── index.md              # 可读索引（按类别列出算法与依赖）
├── sources.json          # 外部来源清单（联网补充用，默认空）
├── manifest_sources.csv  # 抓取记录（fetch_reference_library.py 维护）
├── _common/
│   ├── python/mmlib.py   # 统一演示数据、结果落盘、中文绘图样式
│   └── matlab/mmlib_*.m  # MATLAB 侧同款工具函数
└── <NN_类别>/<算法 id>/
    ├── meta.yaml         # 由 registry.csv 生成：成立条件、常见坑、依赖、接口
    ├── python/main.py    # 最小可运行模板（python main.py）
    ├── matlab/main.m     # 最小可运行模板（matlab -batch "run('main.m')"）
    ├── data/sample.*     # 首次运行自动留档的演示数据
    └── out/              # 运行产物（结果表、图）
```

## 使用方式

1. 在 `manifest.csv` 或 `index.md` 里按算法名/题型定位条目。
2. 读 `meta.yaml` 确认**成立条件**与**常见坑**是否满足；不满足就换算法或补充检验。
3. 读 `python/main.py`（或 `matlab/main.m`）看接口约定与输出形式，然后**按用户题目重写**，不要整段复制。
4. 需要验证模板本身：`python ../scripts/build_library.py --smoke`。

## 维护

- 新增算法：先建目录与两个语言模板，再在 `registry.csv` 增行，最后跑 `build_library.py` 重新生成 `meta.yaml`、`index.md`、`manifest.csv`。
- 依赖由脚本扫描源码自动识别，元数据里不需要手写依赖。
- 外部来源：把 `{name, url, license, target, note}` 写入 `sources.json`，用 `fetch_reference_library.py --plan` 预览、`--fetch` 执行。
- 许可规则：只复制 MIT / BSD / Apache-2.0 / CC0 / 公共领域代码；GPL 类在 `manifest_sources.csv` 里标 `index_only`，不落副本。
