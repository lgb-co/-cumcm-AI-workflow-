% 归一化与标准化（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
X = [100 + 15*randn(50, 1), 0.6 + 0.1*randn(50, 1), 1 + 9*rand(50, 1)];
positive = [true true false];

direction = ones(1, 3); direction(~positive) = -1;
oriented = X .* direction;
minmax = (oriented - min(oriented)) ./ (max(oriented) - min(oriented));
zscore = (oriented - mean(oriented)) ./ std(oriented);

mmlib_report('归一化与标准化', sprintf('样本数=%d', size(X, 1)), sprintf('指标数=%d', size(X, 2)), ...
    sprintf('同向化后均值=%s', mat2str(round(mean(oriented), 4))));
T = array2table(round(minmax, 6), 'VariableNames', "X" + string(1:3));
mmlib_savetable(here, 'minmax_standardization', T);
mmlib_savetable(here, 'zscore_standardization', array2table(round(zscore, 6), ...
    'VariableNames', "X" + string(1:3)));
