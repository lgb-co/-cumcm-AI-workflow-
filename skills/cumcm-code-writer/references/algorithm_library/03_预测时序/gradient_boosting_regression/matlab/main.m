% 梯度提升回归（MATLAB 最小可运行模板，依赖 Statistics and Machine Learning Toolbox）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
X = -2 + 4 * rand(400, 3);
y = exp(X(:, 1)) + sin(2*X(:, 2)) - X(:, 3).^2 + 0.2 * randn(400, 1);

idx = randperm(400); trainIdx = idx(1:300); testIdx = idx(301:end);
model = fitensemble(X(trainIdx, :), y(trainIdx), 'LSBoost', 300, 'Tree', 'LearnRate', 0.05);
pred = predict(model, X(testIdx, :));

rmse = sqrt(mean((pred - y(testIdx)).^2));
R2 = 1 - sum((pred - y(testIdx)).^2) / sum((y(testIdx) - mean(y(testIdx))).^2);

mmlib_report('梯度提升', sprintf('R2=%.4f', R2), sprintf('RMSE=%.4f', rmse), ...
    sprintf('基学习器数=%d', numel(model.Trained)));
T = table((1:numel(pred))', y(testIdx), pred, 'VariableNames', {'样本', '实际值', '预测值'});
mmlib_savetable(here, 'gradient_boosting_regression', T);