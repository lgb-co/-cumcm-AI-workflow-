% Logistic 回归（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
X = randn(500, 3);
logit = 1.5*X(:, 1) - 1.0*X(:, 2) + 0.5*X(:, 3);
y = double(rand(500, 1) < 1 ./ (1 + exp(-logit)));

cv = cvpartition(y, 'HoldOut', 0.3);
mdl = fitglm(X(training(cv), :), y(training(cv)), 'Distribution', 'binomial');
prob = predict(mdl, X(test(cv), :));
[~, ~, ~, auc] = perfcurve(y(test(cv)), prob, 1);
coef = mdl.Coefficients.Estimate;

mmlib_report('Logistic 回归', sprintf('AUC=%.4f', auc), sprintf('系数=%s', mat2str(round(coef', 4))), ...
    sprintf('优势比=%s', mat2str(round(exp(coef)', 4))));
T = table(["常数"; "X1"; "X2"; "X3"], coef, exp(coef), 'VariableNames', {'变量', '系数', 'OR'});
mmlib_savetable(here, 'logistic_regression', T);
