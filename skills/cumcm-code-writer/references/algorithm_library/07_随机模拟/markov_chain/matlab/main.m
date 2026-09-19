% 马尔可夫链预测（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

seq = [0 1 0 1 1 2 1 0 0 1 2 2 1 0 1 1 0 2 1 0];
steps = 6;
states = unique(seq);
n = numel(states);

counts = zeros(n, n);
for k = 1:numel(seq) - 1
    counts(seq(k) + 1, seq(k + 1) + 1) = counts(seq(k) + 1, seq(k + 1) + 1) + 1;
end
P = counts ./ sum(counts, 2);

current = zeros(1, n); current(seq(end) + 1) = 1;
dist = zeros(steps + 1, n); dist(1, :) = current;
for k = 1:steps
    current = current * P;
    dist(k + 1, :) = current;
end
stationary = ones(1, n) / n;
for k = 1:500
    stationary = stationary * P;
end

mmlib_report('马尔可夫链', sprintf('状态数=%d', n), ...
    sprintf('行和校验=%s', mat2str(round(sum(P, 2)', 6))), ...
    sprintf('平稳分布=%s', mat2str(round(stationary, 4))));

period = (0:steps)';
T = table(period, dist(:, 1), dist(:, 2), dist(:, 3), ...
    'VariableNames', {'期数', '状态0', '状态1', '状态2'});
mmlib_savetable(here, 'markov_chain', T);