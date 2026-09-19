% K-means 聚类（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
centersTrue = [0 0; 5 5; -4 4];
X = [];
for i = 1:3
    X = [X; centersTrue(i, :) + 0.8 * randn(60, 2)]; %#ok<AGROW>
end
Xs = zscore(X);

kRange = 2:6; sse = zeros(size(kRange)); sil = zeros(size(kRange));
for i = 1:numel(kRange)
    [idx, ~, sumd] = kmeans(Xs, kRange(i), 'Replicates', 20, 'Display', 'off');
    sse(i) = sum(sumd);
    sil(i) = mean(silhouette(Xs, idx));
end
[~, kBest] = max(sil);

mmlib_report('K-means', sprintf('最优K=%d', kRange(kBest)), ...
    sprintf('轮廓系数=%.4f', sil(kBest)), sprintf('样本数=%d', size(Xs, 1)));
T = table(kRange', sse', sil', 'VariableNames', {'K', 'SSE', '轮廓系数'});
mmlib_savetable(here, 'kmeans', T);
