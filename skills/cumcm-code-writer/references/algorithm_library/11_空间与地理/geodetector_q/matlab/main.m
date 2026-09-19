% 地理探测器 · 因子探测 q 统计量（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
n = 300;
factor = randi(5, n, 1);
y = 10 + 2.5 * factor + 1.5 * randn(n, 1);
noise = randi(3, n, 1);

qMain = geodetector_q(y, factor);
qNoise = geodetector_q(y, noise);

levels = unique(factor);
counts = arrayfun(@(lv) sum(factor == lv), levels);
means = arrayfun(@(lv) mean(y(factor == lv)), levels);

mmlib_report('地理探测器', sprintf('主因子q=%.4f', qMain), sprintf('噪声因子q=%.4f', qNoise), ...
    sprintf('解释力比较=%s', string(qMain > 2 * qNoise)));
T = table(levels, counts, means, 'VariableNames', {'分层', '样本数', '均值'});
mmlib_savetable(here, 'geodetector_q', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）

function q = geodetector_q(y, strata)
totalVar = var(y, 1);
weighted = 0;
for lv = unique(strata)'
    subset = y(strata == lv);
    weighted = weighted + numel(subset) * var(subset, 1);
end
q = 1 - weighted / (numel(y) * totalVar);
end
