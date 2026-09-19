% 层次聚类（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
centers = [0 0; 6 6; -5 5];
X = [];
for i = 1:3
    X = [X; centers(i, :) + 0.7 * randn(40, 2)]; %#ok<AGROW>
end

Z = linkage(X, 'ward');
labels = cluster(Z, 'maxclust', 3);
sil = mean(silhouette(X, labels));

mmlib_report('层次聚类', '簇数=3', sprintf('轮廓系数=%.4f', sil), sprintf('样本数=%d', numel(labels)));
T = table((1:size(Z, 1))', Z(:, 3), 'VariableNames', {'步骤', '合并距离'});
mmlib_savetable(here, 'hierarchical_clustering', T);
