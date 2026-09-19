% 朴素贝叶斯分类（MATLAB 最小可运行模板，依赖 Statistics and Machine Learning Toolbox）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
X = [randn(120, 2) .* [0.8 1.0] + [1 1]; randn(120, 2) .* [1.0 0.8] + [3.5 2]];
y = [zeros(120, 1); ones(120, 1)];

cv = cvpartition(y, 'HoldOut', 0.3);
mdl = fitcnb(X(training(cv), :), y(training(cv)));
[pred, posterior] = predict(mdl, X(test(cv), :));
acc = mean(pred == y(test(cv)));
mu = cellfun(@(c) c(1), mdl.DistributionParameters);

mmlib_report('朴素贝叶斯', sprintf('测试准确率=%.4f', acc), ...
    sprintf('先验=%s', mat2str(round(mdl.Prior, 4))), sprintf('类均值=%s', mat2str(round(mu, 4))));
T = table((1:size(posterior, 1))', posterior(:, 1), posterior(:, 2), y(test(cv)), ...
    'VariableNames', {'样本', 'P_C1', 'P_C2', '真实类别'});
mmlib_savetable(here, 'naive_bayes', T);