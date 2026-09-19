% 模拟退火 SA · 十城市 TSP（MATLAB 最小可运行模板）
% 邻域：2-opt 逆序交换；接受准则：Metropolis。
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

coords = [0 0; 10 0; 20 5; 22 18; 12 26; 0 22; -8 14; -6 4; 8 12; 16 10];
D = squareform(pdist(coords));
n = size(coords, 1);
rng(42);

tour = 1:n; current = tourlen(tour, D); best = current; bestTour = tour;
T = 100; alpha = 0.99; tMin = 0.5; inner = 200; history = [];
while T > tMin && numel(history) < 400
    for k = 1:inner
        ij = sort(randperm(n, 2));
        cand = tour; cand(ij(1):ij(2)) = cand(ij(2):-1:ij(1));
        len = tourlen(cand, D); delta = len - current;
        if delta < 0 || rand() < exp(-delta / T)
            tour = cand; current = len;
            if current < best
                best = current; bestTour = tour;
            end
        end
    end
    T = T * alpha; history(end + 1) = best; %#ok<AGROW>
end

mmlib_report('模拟退火', sprintf('最优路径长度=%.3f', best), ...
    sprintf('巡回顺序=%s', mat2str(bestTour)), sprintf('温度步数=%d', numel(history)));
mmlib_savetable(here, 'simulated_annealing', table((1:numel(history))', history', ...
    'VariableNames', {'温度步', '当前最优'}));

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）

function L = tourlen(tour, D)
idx = [tour tour(1)];
L = sum(D(sub2ind(size(D), idx(1:end-1), idx(2:end))));
end
