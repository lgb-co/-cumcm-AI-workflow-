% 递归特征消除 RFE（MATLAB 最小可运行模板，依赖 Statistics and Machine Learning Toolbox）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
X = randn(400, 8);
score = 1.6*X(:, 1) - 1.2*X(:, 4) + 0.9*X(:, 6) + 0.8*randn(400, 1);
y = double(score > 0);

fun = @(Xtr, ytr, Xte, yte) 1 - mean(predict(fitglm(Xtr, ytr, 'Distribution', 'binomial'), Xte) > 0.5 == yte);
[features, ~] = sequentialfs(fun, X, y, 'cv', cvpartition(y, 'KFold', 5));
kept = find(features);

mmlib_report('递归特征消除', sprintf('保留特征数=%d', numel(kept)), ...
    sprintf('保留特征=%s', mat2str(kept)));
T = table("特征" + string(1:size(X, 2))', double(features'), 'VariableNames', {'特征', '是否保留'});
mmlib_savetable(here, 'rfe_feature_selection', T);
