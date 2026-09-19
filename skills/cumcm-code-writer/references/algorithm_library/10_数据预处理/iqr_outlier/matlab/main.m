% IQR 四分位距异常值检测（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
x = 50 + 5 * randn(120, 1);
x([10 45 90]) = [85; -12; 96];

q = quantile(x, [0.25 0.75]);
iqrValue = q(2) - q(1);
low = q(1) - 1.5 * iqrValue; high = q(2) + 1.5 * iqrValue;
mask = (x < low) | (x > high);

mmlib_report('IQR 异常检测', sprintf('下界=%.3f', low), sprintf('上界=%.3f', high), ...
    sprintf('异常点数=%d', sum(mask)), sprintf('异常比例=%.1f%%', mean(mask) * 100));
T = table((1:numel(x))', x, double(mask), 'VariableNames', {'序号', '数值', '是否异常'});
mmlib_savetable(here, 'iqr_outlier', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
