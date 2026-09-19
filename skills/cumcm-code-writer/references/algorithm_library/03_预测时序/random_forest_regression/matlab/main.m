% 随机森林回归（MATLAB 最小可运行模板，依赖 Statistics and Machine Learning Toolbox）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
X = randn(300, 5);
y = 2*X(:, 1) + X(:, 2).^2 - 1.5*X(:, 3) + 0.4*randn(300, 1);

idx = randperm(300); trainIdx = idx(1:225); testIdx = idx(226:end);
model = TreeBagger(300, X(trainIdx, :), y(trainIdx), 'Method', 'regression', ...
    'OOBPrediction', 'on', 'OOBPredictorImportance', 'on');
pred = predict(model, X(testIdx, :));

rmse = sqrt(mean((pred - y(testIdx)).^2));
R2 = 1 - sum((pred - y(testIdx)).^2) / sum((y(testIdx) - mean(y(testIdx))).^2);
imp = model.OOBPermutedPredictorDeltaError;

mmlib_report('随机森林', sprintf('R2=%.4f', R2), sprintf('RMSE=%.4f', rmse), ...
    sprintf('特征重要性=%s', mat2str(round(imp, 4))));
T = table("X" + string(1:numel(imp))', imp', 'VariableNames', {'特征', '重要性'});
mmlib_savetable(here, 'random_forest_regression', T);