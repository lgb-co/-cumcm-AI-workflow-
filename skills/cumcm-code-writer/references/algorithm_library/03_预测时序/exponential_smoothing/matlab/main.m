% 指数平滑预测 · Holt 线性趋势（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
t = (0:59)';
series = 50 + 0.8*t + 1.5*randn(60, 1);
steps = 6;

bestRmse = inf; bestF = []; bestParams = [0 0];
for alpha = 0.05:0.05:0.95
    for beta = 0.05:0.05:0.95
        level = series(1); trend = series(2) - series(1); fitted = level;
        for i = 2:numel(series)
            last = level;
            level = alpha*series(i) + (1-alpha)*(level + trend);
            trend = beta*(level - last) + (1-beta)*trend;
            fitted(end + 1, 1) = level + trend; %#ok<AGROW>
        end
        rmse = sqrt(mean((fitted - series).^2));
        if rmse < bestRmse
            bestRmse = rmse;
            bestF = arrayfun(@(h) level + (h + 1)*trend, 1:steps)';
            bestParams = [alpha beta];
        end
    end
end

mmlib_report('指数平滑', sprintf('alpha=%.2f', bestParams(1)), sprintf('beta=%.2f', bestParams(2)), ...
    sprintf('拟合RMSE=%.4f', bestRmse), sprintf('预测值=%s', mat2str(round(bestF', 4))));
T = table((1:steps)', bestF, 'VariableNames', {'期数', '预测值'});
mmlib_savetable(here, 'exponential_smoothing', T);
