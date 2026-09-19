% 回归诊断（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
X = randn(120, 3);
X(:, 3) = 0.85 * X(:, 1) + 0.3 * randn(120, 1);
y = 1.0 + X * [1.5; -0.9; 0.6] + randn(120, 1);

mdl = fitlm(X, y);
residuals = mdl.Residuals.Raw;
[~, shapiroP] = swtest(residuals);
vifValues = diag(inv(corrcoef(X)));
cooks = mdl.Diagnostics.CooksDistance;

mmlib_report('回归诊断', sprintf('R2=%.4f', mdl.Rsquared.Ordinary), ...
    sprintf('残差正态性p=%.4f', shapiroP), sprintf('最大VIF=%.3f', max(vifValues)), ...
    sprintf('异常点数=%d', sum(cooks > 4 / numel(y))));
T = table(["常数"; "X1"; "X2"; "X3"], mdl.Coefficients.Estimate, mdl.Coefficients.SE, ...
    mdl.Coefficients.tStat, mdl.Coefficients.pValue, ...
    'VariableNames', {'变量', '系数', '标准误', 't值', 'p值'});
mmlib_savetable(here, 'regression_diagnostics', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）

function [h, p] = swtest(x)
% 轻量正态性检验替代：Shapiro-Wilk 需要工具支持，这里用偏度峰度联合检验(JB)。
[h, p] = jbtest(x);
end
