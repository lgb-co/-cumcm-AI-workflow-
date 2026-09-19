% DBSCAN 密度聚类（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
X = [randn(70, 2) * 0.5; randn(60, 2) * 0.6 + 4; -6 + 12 * rand(10, 2)];
Xs = zscore(X);

k = 5;
[~, dists] = knnsearch(Xs, Xs, 'K', k);
kth = sort(dists(:, end));
grad = gradient(kth);
epsEst = kth(find(grad == max(grad), 1));

labels = dbscan(Xs, epsEst, k);
clusters = numel(unique(labels(labels > 0)));
noise = sum(labels == -1);

mmlib_report('DBSCAN', sprintf('eps=%.4f', epsEst), sprintf('簇数=%d', clusters), sprintf('噪声点=%d', noise));
T = table((1:numel(labels))', labels, X(:, 1), X(:, 2), 'VariableNames', {'样本', '标签', 'X1', 'X2'});
mmlib_savetable(here, 'dbscan', T);
