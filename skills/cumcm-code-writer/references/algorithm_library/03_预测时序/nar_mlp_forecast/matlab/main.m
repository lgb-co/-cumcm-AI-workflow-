% NAR 非线性自回归神经网络预测（MATLAB 最小可运行模板）
% 说明：本机无 Deep Learning Toolbox，用单隐藏层 ELM（随机隐层 + 最小二乘输出）实现同样的"滞后特征回归"。
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
t = (0:119)';
series = 30 + 6*sin(2*pi*t/24) + 0.05*t + 0.4*randn(120, 1);
lags = 6; steps = 12;

X = zeros(numel(series) - lags, lags);
for k = 1:lags
    X(:, k) = series(lags - k + 1:end - k);
end
y = series(lags + 1:end);
split = round(0.8 * size(X, 1));

hidden = 16;
W = randn(lags, hidden); b = randn(1, hidden);
H = 2 ./ (1 + exp(-2 * (X * W + b))) - 1;
beta = pinv(H(1:split, :)) * y(1:split);
fitted = H * beta;
rmse = sqrt(mean((fitted(split + 1:end) - y(split + 1:end)).^2));

window = series(end - lags + 1:end);
forecast = zeros(steps, 1);
for h = 1:steps
    feat = flipud(window(end - lags + 1:end));              % lags×1
    hiddenOut = 2 ./ (1 + exp(-2 * (W' * feat + b'))) - 1;  % hidden×1
    value = beta' * hiddenOut;                              % 1×1
    forecast(h) = value;
    window = [window; value]; %#ok<AGROW>
end

mmlib_report('NAR 神经网络', sprintf('滞后阶数=%d', lags), sprintf('留出RMSE=%.4f', rmse), ...
    sprintf('预测首期=%.4f', forecast(1)), sprintf('预测末期=%.4f', forecast(end)));
T = table([y; forecast], 'VariableNames', {'数值'});
mmlib_savetable(here, 'nar_mlp_forecast', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
