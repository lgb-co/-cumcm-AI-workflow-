% 相关分析 · Pearson / Spearman（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
x1 = randn(120, 1);
X = [x1, 0.7*x1 + 0.7*randn(120, 1), exp(x1/2) + 0.3*randn(120, 1), randn(120, 1)];

pearson = corr(X, 'Type', 'Pearson');
spearman = corr(X, 'Type', 'Spearman');
[~, pValues] = corr(X, 'Type', 'Pearson');

mmlib_report('相关分析', sprintf('样本量=%d', size(X, 1)), ...
    sprintf('X1-X2 Pearson=%.4f', pearson(1, 2)), sprintf('X1-X3 Spearman=%.4f', spearman(1, 3)));
T = array2table(round(pearson, 6), 'VariableNames', "X" + string(1:4));
mmlib_savetable(here, 'correlation_analysis', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
