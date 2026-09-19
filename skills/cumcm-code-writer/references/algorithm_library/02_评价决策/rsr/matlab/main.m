% 秩和比 RSR · 综合评价与分档（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

X = [92 0.83 3.1 8; 78 0.71 4.5 6; 85 0.90 2.7 9; 70 0.64 5.2 5; 88 0.79 3.6 7];
positive = [true true false true];
w = [0.3 0.3 0.2 0.2];
n = size(X, 1); m = size(X, 2);

R = zeros(n, m);
for j = 1:m
    col = X(:, j);
    if ~positive(j)
        col = -col;
    end
    [~, idx] = sort(col);
    r = zeros(n, 1);
    r(idx) = 1:n;
    R(:, j) = r;
end
rsr = (R * w') / n;
[~, order] = sort(rsr, 'descend');
rank = zeros(n, 1); rank(order) = 1:n;

mmlib_report('秩和比', sprintf('RSR=%s', mat2str(round(rsr', 4))), sprintf('排序=%s', mat2str(rank')));
T = table("A" + string(1:n)', rsr, rank, 'VariableNames', {'方案', 'RSR', '排序'});
mmlib_savetable(here, 'rsr', T);
