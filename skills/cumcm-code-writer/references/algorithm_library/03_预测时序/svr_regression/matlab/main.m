% 支持向量回归 SVR（MATLAB 最小可运行模板，依赖 Statistics and Machine Learning Toolbox）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
X = -3 + 6 * rand(160, 2);
y = exp(-0.5 * X(:, 1).^2) + 0.4 * sin(2 * X(:, 2)) + 0.05 * randn(160, 1);

idx = randperm(160); trainIdx = idx(1:112); testIdx = idx(113:end);
bestRMSE = inf; bestModel = [];
for C = [0.1 1 10 100]
    for gamma = [0.1 0.5 1]
        mdl = fitrsvm(X(trainIdx, :), y(trainIdx), 'KernelFunction', 'rbf', ...
            'BoxConstraint', C, 'KernelScale', 1 / sqrt(gamma), 'Standardize', true);
        pred = predict(mdl, X(testIdx, :));
        rmse = sqrt(mean((pred - y(testIdx)).^2));
        if rmse < bestRMSE
            bestRMSE = rmse; bestModel = mdl; bestC = C; bestGamma = gamma; %#ok<NASGU>
        end
    end
end
pred = predict(bestModel, X(testIdx, :));
R2 = 1 - sum((pred - y(testIdx)).^2) / sum((y(testIdx) - mean(y(testIdx))).^2);

mmlib_report('支持向量回归', sprintf('R2=%.4f', R2), sprintf('RMSE=%.4f', bestRMSE), ...
    sprintf('支持向量数=%d', numel(bestModel.SupportVectors)));
T = table((1:numel(pred))', y(testIdx), pred, 'VariableNames', {'样本', '实际值', '预测值'});
mmlib_savetable(here, 'svr_regression', T);
