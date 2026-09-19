% 岭回归 · 共线性下的正则化回归（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
X = randn(80, 4);
X(:, 4) = 0.95 * X(:, 1) + 0.1 * randn(80, 1);
y = 1.5 + X * [1; -0.6; 0.4; 0.8] + 0.4 * randn(80, 1);

alphas = logspace(-3, 2, 30);
rmse = zeros(size(alphas));
for k = 1:numel(alphas)
    b = ridge(y, X, alphas(k), 0);
    pred = [ones(size(X, 1), 1) X] * b;
    rmse(k) = sqrt(mean((y - pred).^2));
end
[~, kBest] = min(rmse);
beta = ridge(y, X, alphas(kBest), 0);

mmlib_report('岭回归', sprintf('最优lambda=%.4g', alphas(kBest)), ...
    sprintf('系数=%s', mat2str(round(beta', 4))), sprintf('RMSE=%.4f', rmse(kBest)));
T = table(alphas', rmse', 'VariableNames', {'lambda', 'RMSE'});
mmlib_savetable(here, 'ridge_regression', T);
