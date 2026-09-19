% t-SNE 高维数据可视化（MATLAB 最小可运行模板，依赖 Statistics and Machine Learning Toolbox）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
X = []; labels = [];
shifts = [0 2 4];
for k = 1:3
    X = [X; randn(80, 8) * 0.8 + shifts(k)]; %#ok<AGROW>
    labels = [labels; k * ones(80, 1)]; %#ok<AGROW>
end
X = zscore(X);

embedding = tsne(X, 'Perplexity', 30, 'NumDimensions', 2);

mmlib_report('t-SNE', '困惑度=30', sprintf('样本数=%d', size(embedding, 1)));
T = table((1:size(embedding, 1))', embedding(:, 1), embedding(:, 2), labels, ...
    'VariableNames', {'样本', 'T1', 'T2', '类别'});
mmlib_savetable(here, 'tsne', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
