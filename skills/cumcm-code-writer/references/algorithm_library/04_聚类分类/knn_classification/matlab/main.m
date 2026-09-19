% KNN 分类（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
X = [randn(80, 2) * 0.9; randn(80, 2) * 0.9 + 3; randn(80, 2) * 0.9 + [0 4]];
y = [zeros(80, 1); ones(80, 1); 2 * ones(80, 1)];

cv = cvpartition(y, 'HoldOut', 0.3);
Xtrain = X(training(cv), :); ytrain = y(training(cv));
Xtest = X(test(cv), :); ytest = y(test(cv));

kRange = [1 3 5 7 9 11]; acc = zeros(size(kRange));
for i = 1:numel(kRange)
    mdl = fitcknn(Xtrain, ytrain, 'NumNeighbors', kRange(i), 'Standardize', true);
    acc(i) = 1 - loss(mdl, Xtest, ytest);
end
[bestAcc, kBest] = max(acc);

mmlib_report('KNN 分类', sprintf('最优K=%d', kRange(kBest)), sprintf('测试准确率=%.4f', bestAcc));
T = table(kRange', acc', 'VariableNames', {'K', '准确率'});
mmlib_savetable(here, 'knn_classification', T);
