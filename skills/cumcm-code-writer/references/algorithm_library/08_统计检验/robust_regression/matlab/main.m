% 稳健回归 · Huber M 估计（MATLAB 最小可运行模板，依赖 Statistics and Machine Learning Toolbox）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
X = randn(200, 3);
y = 1.0 + X * [2; -1.5; 0.8] + 0.5 * randn(200, 1);
outliers = randperm(200, 12)';
y(outliers) = y(outliers) + 12 + 3 * randn(12, 1);

ols = fitlm(X, y);
robust = fitlm(X, y, 'RobustOpts', 'on');
olsCoef = ols.Coefficients.Estimate;
robustCoef = robust.Coefficients.Estimate;

mmlib_report('稳健回归', sprintf('Huber系数=%s', mat2str(round(robustCoef', 4))), ...
    sprintf('OLS系数=%s', mat2str(round(olsCoef', 4))), ...
    sprintf('系数最大差异=%.4f', max(abs(robustCoef - olsCoef))));
T = table(["常数"; "X1"; "X2"; "X3"], robustCoef, olsCoef, robustCoef - olsCoef, ...
    'VariableNames', {'变量', 'Huber', 'OLS', '差异'});
mmlib_savetable(here, 'robust_regression', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
