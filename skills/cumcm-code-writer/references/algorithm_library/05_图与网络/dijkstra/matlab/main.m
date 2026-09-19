% Dijkstra 最短路（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

edges = [0 1 4; 0 2 2; 1 2 1; 1 3 5; 2 3 8; 2 4 10; 3 4 2; 3 5 6; 4 5 3];
n = 6; source = 1;   % MATLAB 节点编号从 1 开始，对应 Python 的 0 号节点

G = graph(edges(:, 1) + 1, edges(:, 2) + 1, edges(:, 3));
[tree, dist] = shortestpathtree(G, source);
prevIdx = nan(1, n);
for k = 1:n
    if k == source, continue; end
    path = shortestpath(G, source, k);
    if numel(path) >= 2
        prevIdx(k) = path(end - 1) - 1;
    end
end
assert(~isempty(tree) && numel(dist) == n);

mmlib_report('Dijkstra', sprintf('源点=%d', source - 1), ...
    sprintf('最短路=%s', mat2str(round(dist, 3))));
T = table((0:n-1)', dist(:), prevIdx', 'VariableNames', {'节点', '距离', '前驱'});
mmlib_savetable(here, 'dijkstra', T);