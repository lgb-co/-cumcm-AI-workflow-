% Z-Score 异常值检测（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
x = 100 + 8 * randn(150, 1);
x([5 77 140]) = [150; 40; 155];

z = (x - mean(x)) / std(x);
threshold = 3;
mask = abs(z) > threshold;

mmlib_report('Z-Score 异常检测', sprintf('阈值=%.1f', threshold), ...
    sprintf('异常点数=%d', sum(mask)), sprintf('最大|z|=%.3f', max(abs(z))));
T = table((1:numel(x))', x, z, double(mask), 'VariableNames', {'序号', '数值', 'Z值', '是否异常'});
mmlib_savetable(here, 'zscore_outlier', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
