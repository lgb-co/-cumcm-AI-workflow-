% ARIMA(p,1,0) 时间序列预测（MATLAB 最小可运行模板，无工具箱依赖）
% 做法：一阶差分后按滞后阶 p 做最小二乘估计 AR 系数，再递推多步预测；p 由 BIC 在 0..4 中选取。
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
t = (0:119)';
series = 20 + 0.15*t + 3*sin(2*pi*t/12) + 0.8*randn(120, 1);
steps = 12;
diffSeries = diff(series);

bestP = 0; bestModel = []; bestBIC = inf;
for p = 0:4
    if p == 0
        residuals = diffSeries - mean(diffSeries);
        sse = sum(residuals.^2);
        model = struct('p', 0, 'c', mean(diffSeries), 'phi', []);
    else
        n = numel(diffSeries);
        Y = diffSeries(p + 1:end);
        X = ones(n - p, 1);
        for lag = 1:p
            X = [X diffSeries(p + 1 - lag:end - lag)]; %#ok<AGROW>
        end
        coef = X \ Y;
        residuals = Y - X * coef;
        sse = sum(residuals.^2);
        model = struct('p', p, 'c', coef(1), 'phi', coef(2:end)');
    end
    bic = numel(residuals) * log(sse / numel(residuals)) + (p + 1) * log(numel(residuals));
    if bic < bestBIC
        bestBIC = bic; bestP = p; bestModel = model;
    end
end

history = diffSeries;
forecastDiff = zeros(steps, 1);
for h = 1:steps
    value = bestModel.c;
    for lag = 1:bestModel.p
        value = value + bestModel.phi(lag) * history(end - lag + 1);
    end
    forecastDiff(h) = value;
    history = [history; value]; %#ok<AGROW>
end
forecastY = series(end) + cumsum(forecastDiff);

mmlib_report('ARIMA(1,1,0)', sprintf('差分阶数=1'), sprintf('AR阶数=%d', bestP), ...
    sprintf('BIC=%.2f', bestBIC), sprintf('预测首期=%.4f', forecastY(1)), ...
    sprintf('预测末期=%.4f', forecastY(end)));
T = table((1:steps)', forecastY, 'VariableNames', {'期数', '预测值'});
mmlib_savetable(here, 'arima_forecast', T);