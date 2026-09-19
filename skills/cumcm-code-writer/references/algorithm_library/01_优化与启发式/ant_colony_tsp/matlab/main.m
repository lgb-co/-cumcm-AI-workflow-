% 蚁群算法 ACO · 十城市 TSP（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

coords = [0 0; 10 0; 20 5; 22 18; 12 26; 0 22; -8 14; -6 4; 8 12; 16 10];
D = squareform(pdist(coords));
n = size(coords, 1);
ants = 10; iterations = 120; alpha = 1; beta = 2; rho = 0.5; q = 1;
tau = ones(n, n);
eta = 1 ./ (D + eye(n));
rng(42);
best = inf; bestTour = 1:n; history = zeros(iterations, 1);

for it = 1:iterations
    tours = zeros(ants, n); lengths = zeros(ants, 1);
    for k = 1:ants
        start = randi(n);
        tour = start; visited = false(1, n); visited(start) = true;
        while numel(tour) < n
            cur = tour(end);
            prob = (tau(cur, :) .^ alpha) .* (eta(cur, :) .^ beta);
            prob(visited) = 0;
            prob = prob / sum(prob);
            nxt = find(rand() <= cumsum(prob), 1);
            tour(end + 1) = nxt; %#ok<AGROW>
            visited(nxt) = true;
        end
        tours(k, :) = tour;
        idx = [tour tour(1)];
        lengths(k) = sum(D(sub2ind(size(D), idx(1:end-1), idx(2:end))));
    end
    tau = (1 - rho) * tau;
    for k = 1:ants
        idx = [tours(k, :) tours(k, 1)];
        for m = 1:n
            tau(idx(m), idx(m + 1)) = tau(idx(m), idx(m + 1)) + q / lengths(k);
        end
    end
    [curBest, kBest] = min(lengths);
    if curBest < best
        best = curBest; bestTour = tours(kBest, :);
    end
    history(it) = best;
end

mmlib_report('蚁群算法', sprintf('最优路径长度=%.3f', best), ...
    sprintf('巡回顺序=%s', mat2str(bestTour)), sprintf('迭代=%d', iterations));
mmlib_savetable(here, 'ant_colony_tsp', table((1:iterations)', history, 'VariableNames', {'迭代', '当前最优'}));

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
