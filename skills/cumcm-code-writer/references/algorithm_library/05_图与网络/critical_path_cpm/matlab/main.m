% 关键路径 CPM（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

A = [0 1 3; 0 2 4; 1 3 5; 2 3 2; 1 4 6; 3 5 4; 4 5 3; 4 6 5; 5 6 2];
n = 7; nodes = A(:, 1:2) + 1; dur = A(:, 3);

G = digraph(nodes(:, 1), nodes(:, 2), dur);
order = toposort(G);
ES = zeros(n, 1);
for k = 1:numel(order)
    u = order(k);
    for e = 1:size(A, 1)
        if nodes(e, 1) == u
            v = nodes(e, 2);
            ES(v) = max(ES(v), ES(u) + dur(e));
        end
    end
end
T0 = max(ES);
LF = T0 * ones(n, 1);
for k = numel(order):-1:1
    u = order(k);
    for e = 1:size(A, 1)
        if nodes(e, 1) == u
            v = nodes(e, 2);
            LF(u) = min(LF(u), LF(v) - dur(e));
        end
    end
end
slack = LF - ES;
critical = find(abs(slack) < 1e-9)' - 1;

mmlib_report('关键路径', sprintf('总工期=%.3f', T0), sprintf('关键节点=%s', mat2str(critical)));
T = table((0:n-1)', ES, LF, slack, 'VariableNames', {'节点', '最早开始', '最迟完成', '总时差'});
mmlib_savetable(here, 'critical_path_cpm', T);
