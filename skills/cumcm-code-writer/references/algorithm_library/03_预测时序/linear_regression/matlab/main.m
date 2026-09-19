% 多元线性回归 · 影响因素建模（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
X = randn(60, 3);
y = 2.5 + X * [1.2; -0.8; 0.5] + 0.3 * randn(60, 1);

mdl = fitlm(X, y);
pred = predict(mdl, X);
r2 = mdl.Rsquared.Ordinary;
rmse = sqrt(mean((y - pred).^2));

mmlib_report('多元线性回归', sprintf('系数=%s', mat2str(round(mdl.Coefficients.Estimate', 4))), ...
    sprintf('R2=%.4f', r2), sprintf('RMSE=%.4f', rmse));
T = table((1:numel(y))', y, pred, 'VariableNames', {'样本', '实际值', '预测值'});
mmlib_savetable(here, 'linear_regression', T);
