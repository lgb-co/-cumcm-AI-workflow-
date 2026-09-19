% BP 神经网络（MLP）回归（MATLAB 最小可运行模板）
% 说明：本机未装 Deep Learning Toolbox，这里用极限学习机(ELM)等价演示"单隐藏层 + 最小二乘输出"。
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
X = -3 + 6 * rand(200, 2);
y = sin(X(:, 1)) + 0.5 * X(:, 2).^2 + 0.1 * randn(200, 1);

idx = randperm(200); trainIdx = idx(1:150); testIdx = idx(151:end);
Xtrain = X(trainIdx, :); Xtest = X(testIdx, :);

hidden = 16;
W = randn(2, hidden); b = randn(1, hidden);
H = 2 ./ (1 + exp(-2 * (Xtrain * W + b))) - 1;   % tanh 激活，避免依赖工具箱
beta = pinv(H) * y(trainIdx);                     % 输出层最小二乘
pred = (2 ./ (1 + exp(-2 * (Xtest * W + b))) - 1) * beta;

rmse = sqrt(mean((pred - y(testIdx)).^2));
R2 = 1 - sum((pred - y(testIdx)).^2) / sum((y(testIdx) - mean(y(testIdx))).^2);

mmlib_report('MLP/ELM 回归', sprintf('R2=%.4f', R2), sprintf('RMSE=%.4f', rmse), ...
    sprintf('测试样本=%d', numel(pred)));
T = table((1:numel(pred))', y(testIdx), pred, 'VariableNames', {'样本', '实际值', '预测值'});
mmlib_savetable(here, 'mlp_regression', T);