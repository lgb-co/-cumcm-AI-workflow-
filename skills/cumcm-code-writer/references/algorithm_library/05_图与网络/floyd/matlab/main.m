% Floyd 全源最短路（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

edges = [0 1 4; 0 2 2; 1 2 1; 1 3 5; 2 3 8; 2 4 10; 3 4 2; 3 5 6; 4 5 3];
n = 6;

D = inf(n);
D(1:n+1:end) = 0;
for k = 1:size(edges, 1)
    u = edges(k, 1) + 1; v = edges(k, 2) + 1; w = edges(k, 3);
    D(u, v) = min(D(u, v), w); D(v, u) = D(u, v);
end
for k = 1:n
    D = min(D, D(:, k) + D(k, :));
end

diameter = max(D(isfinite(D)));
mmlib_report('Floyd', sprintf('节点数=%d', n), sprintf('网络直径=%.3f', diameter));
T = table(repelem((1:n)', n), repmat((1:n)', n, 1), D(:), 'VariableNames', {'起点', '终点', '距离'});
mmlib_savetable(here, 'floyd', T);
