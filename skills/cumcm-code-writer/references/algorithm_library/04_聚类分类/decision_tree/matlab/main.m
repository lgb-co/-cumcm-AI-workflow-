% 决策树分类（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
X = randn(400, 4);
score = 1.2*X(:, 1) - 0.8*X(:, 2) + 0.5*X(:, 3) + 0.5*randn(400, 1);
y = double(score > 0);

cv = cvpartition(y, 'HoldOut', 0.3);
mdl = fitctree(X(training(cv), :), y(training(cv)), 'MinLeafSize', 8);
mdl = prune(mdl, 'Level', max(0, max(mdl.PruneList) - 2));
pred = predict(mdl, X(test(cv), :));
acc = mean(pred == y(test(cv)));
imp = predictorImportance(mdl);

mmlib_report('决策树', sprintf('测试准确率=%.4f', acc), sprintf('树深度=%d', max(mdl.PruneList)), ...
    sprintf('特征重要性=%s', mat2str(round(imp, 4))));
T = table("指标" + string(1:numel(imp))', imp', 'VariableNames', {'特征', '重要性'});
mmlib_savetable(here, 'decision_tree', T);
