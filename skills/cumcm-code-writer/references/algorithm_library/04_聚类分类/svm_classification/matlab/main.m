% 支持向量机分类（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
X = [randn(90, 2) + [-1.5 -1.5]; randn(90, 2) + [1.5 1.5]];
y = [zeros(90, 1); ones(90, 1)];

cv = cvpartition(y, 'HoldOut', 0.3);
bestAcc = 0; bestMdl = [];
for C = [0.1 1 10]
    for gamma = [0.1 1]
        mdl = fitcsvm(X(training(cv), :), y(training(cv)), 'KernelFunction', 'rbf', ...
            'BoxConstraint', C, 'KernelScale', 1 / sqrt(gamma), 'Standardize', true);
        acc = 1 - loss(mdl, X(test(cv), :), y(test(cv)));
        if acc > bestAcc
            bestAcc = acc; bestMdl = mdl;
        end
    end
end
ratio = numel(bestMdl.SupportVectors) / sum(training(cv));

mmlib_report('SVM 分类', sprintf('测试准确率=%.4f', bestAcc), sprintf('支持向量占比=%.4f', ratio));
T = table((1:sum(test(cv)))', y(test(cv)), predict(bestMdl, X(test(cv), :)), ...
    'VariableNames', {'样本', '真实', '预测'});
mmlib_savetable(here, 'svm_classification', T);
