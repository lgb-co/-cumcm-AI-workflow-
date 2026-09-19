% 最小生成树 Kruskal（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

edges = [0 1 4; 0 2 3; 1 2 1; 1 3 2; 2 3 4; 2 4 6; 3 4 5; 3 5 7; 4 5 2];
n = 6;

G = graph(edges(:, 1) + 1, edges(:, 2) + 1, edges(:, 3));
[T, totalWeight] = minspantree(G);

mmlib_report('最小生成树', sprintf('边数=%d', size(T.Edges, 1)), sprintf('总权重=%.3f', totalWeight));
Tout = table(T.Edges.EndNodes(:, 1) - 1, T.Edges.EndNodes(:, 2) - 1, T.Edges.Weight, ...
    'VariableNames', {'起点', '终点', '权重'});
mmlib_savetable(here, 'minimum_spanning_tree', Tout);
