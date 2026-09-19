% 最大流 · Edmonds-Karp（MATLAB 最小可运行模板，纯数组实现，不依赖图论工具箱版本差异）
% 模型：反复用 BFS 寻找增广路，直到不存在增广路；容量矩阵为 0 表示无边。
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

C = [0 16 13 0 0 0; 0 0 10 12 0 0; 0 4 0 0 14 0; 0 0 9 0 0 20; 0 0 0 7 0 4; 0 0 0 0 0 0];
n = size(C, 1); source = 1; sink = 6;

residual = C; flow = zeros(n, n); total = 0;
while true
    parent = zeros(1, n); parent(source) = source;
    queue = source;
    while ~isempty(queue) && parent(sink) == 0
        u = queue(1); queue(1) = [];
        for v = 1:n
            if parent(v) == 0 && residual(u, v) > 1e-12
                parent(v) = u; queue(end + 1) = v; %#ok<AGROW>
            end
        end
    end
    if parent(sink) == 0
        break
    end
    pathFlow = inf; v = sink;
    while v ~= source
        u = parent(v);
        pathFlow = min(pathFlow, residual(u, v));
        v = u;
    end
    v = sink;
    while v ~= source
        u = parent(v);
        flow(u, v) = flow(u, v) + pathFlow;
        flow(v, u) = flow(v, u) - pathFlow;
        residual(u, v) = residual(u, v) - pathFlow;
        residual(v, u) = residual(v, u) + pathFlow;
        v = u;
    end
    total = total + pathFlow;
end

mmlib_report('最大流', sprintf('源点=%d', source - 1), sprintf('汇点=%d', sink - 1), ...
    sprintf('最大流=%.3f', total));
[s, t] = find(C > 0);
T = table(s - 1, t - 1, C(sub2ind(size(C), s, t)), flow(sub2ind(size(C), s, t)), ...
    'VariableNames', {'起点', '终点', '容量', '流量'});
mmlib_savetable(here, 'max_flow', T);