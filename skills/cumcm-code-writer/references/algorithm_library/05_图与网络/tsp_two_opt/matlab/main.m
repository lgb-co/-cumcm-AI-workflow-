% TSP 两阶段启发式 · 最近邻 + 2-opt（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

coords = [0 0; 10 0; 20 5; 22 18; 12 26; 0 22; -8 14; -6 4; 8 12; 16 10];
D = squareform(pdist(coords));
n = size(coords, 1);

tour = 1; visited = false(1, n); visited(1) = true;
while numel(tour) < n
    candidates = find(~visited);
    [~, k] = min(D(tour(end), candidates));
    tour(end + 1) = candidates(k); %#ok<AGROW>
    visited(candidates(k)) = true;
end
initialLength = tourlen(tour, D);
best = tour; bestLength = initialLength; improvements = 0; improved = true;
while improved
    improved = false;
    for i = 2:n-1
        for j = i+1:n
            cand = best; cand(i:j) = cand(j:-1:i);
            len = tourlen(cand, D);
            if len < bestLength - 1e-9
                best = cand; bestLength = len; improvements = improvements + 1; improved = true;
            end
        end
    end
end

mmlib_report('TSP 两阶段', sprintf('初始长度=%.3f', initialLength), ...
    sprintf('优化后长度=%.3f', bestLength), sprintf('改进次数=%d', improvements));
T = table((1:n)', best', 'VariableNames', {'顺序', '城市'});
mmlib_savetable(here, 'tsp_two_opt', T);

function L = tourlen(tour, D)
idx = [tour tour(1)];
L = sum(D(sub2ind(size(D), idx(1:end-1), idx(2:end))));
end
