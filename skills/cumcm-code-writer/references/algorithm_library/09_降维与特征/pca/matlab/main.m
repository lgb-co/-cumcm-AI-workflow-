% 主成分分析 PCA（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
latent = randn(200, 2);
X = latent * [0.9 0.4 0.2 0.1 0.0; 0.1 0.5 0.8 0.3 0.2] + 0.4 * randn(200, 5);

[coeff, score, ~, ~, explained] = pca(X);
cumulative = cumsum(explained);
kept = find(cumulative >= 85, 1);

mmlib_report('主成分分析', sprintf('保留主成分数=%d', kept), ...
    sprintf('累计贡献率=%.4f', cumulative(kept)), ...
    sprintf('各主成分贡献率=%s', mat2str(round(explained(1:kept)', 4))));
T = table("PC" + string(1:numel(explained))', explained, cumulative, ...
    'VariableNames', {'主成分', '贡献率', '累计贡献率'});
mmlib_savetable(here, 'pca', T);
mmlib_savetable(here, 'pca_loadings', array2table(round(coeff(:, 1:kept), 6), ...
    'VariableNames', "PC" + string(1:kept)));

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
