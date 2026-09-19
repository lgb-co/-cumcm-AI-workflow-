% 多项式拟合 · 趋势外推（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
x = linspace(0, 10, 40)';
y = 1.2*x - 0.08*x.^2 + 0.003*x.^3 + 0.2*randn(40, 1);
holdout = 8;
degrees = 1:5;
rmse = zeros(size(degrees));
coefs = cell(size(degrees));

for k = 1:numel(degrees)
    p = polyfit(x(1:end-holdout), y(1:end-holdout), degrees(k));
    rmse(k) = sqrt(mean((polyval(p, x(end-holdout+1:end)) - y(end-holdout+1:end)).^2));
    coefs{k} = p;
end
[bestRmse, kBest] = min(rmse);
p = coefs{kBest};

mmlib_report('多项式拟合', sprintf('最优阶数=%d', degrees(kBest)), sprintf('测试RMSE=%.4f', bestRmse), ...
    sprintf('系数=%s', mat2str(round(p, 6))));
T = table(degrees', rmse', 'VariableNames', {'阶数', '测试RMSE'});
mmlib_savetable(here, 'polynomial_fit', T);
