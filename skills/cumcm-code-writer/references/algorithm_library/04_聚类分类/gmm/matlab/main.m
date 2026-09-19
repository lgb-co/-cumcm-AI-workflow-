% 高斯混合模型 GMM 软聚类（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
X = [randn(80, 2) .* [0.6 1.2]; randn(70, 2) .* [1.0 0.5] + [4 3]];
Xs = zscore(X);

kRange = 2:4; bic = zeros(size(kRange)); models = cell(size(kRange));
for i = 1:numel(kRange)
    models{i} = fitgmdist(Xs, kRange(i), 'Replicates', 5, 'RegularizationValue', 1e-6);
    bic(i) = models{i}.BIC;
end
[~, kBest] = min(bic);
mdl = models{kBest};
[~, ~, posterior] = cluster(mdl, Xs);

mmlib_report('高斯混合', sprintf('最优K=%d', kRange(kBest)), sprintf('BIC=%.3f', bic(kBest)), ...
    sprintf('最大后验概率均值=%.4f', mean(max(posterior, [], 2))));
T = table(kRange', bic', 'VariableNames', {'K', 'BIC'});
mmlib_savetable(here, 'gmm', T);
