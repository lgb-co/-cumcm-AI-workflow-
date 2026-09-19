% NSGA-II · 双目标优化（MATLAB 最小可运行模板）
% 模型：min f1 = sum(x.^2), min f2 = sum((x-2).^2)，x∈[0,2]，n=10
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

dims = 10; low = 0; high = 2; popSize = 40; generations = 30;
obj = @(P) [sum(P.^2, 2), sum((P - 2).^2, 2)];
rng(42);
pop = low + (high - low) * rand(popSize, dims);
objs = obj(pop);

for g = 1:generations
    [fronts, rank] = ndsort(objs);
    crowd = zeros(popSize, 1);
    for f = 1:numel(fronts)
        crowd(fronts{f}) = crowdDist(objs, fronts{f});
    end
    children = zeros(popSize, dims);
    for k = 1:2:popSize
        a1 = tournament(rank, crowd);
        a2 = tournament(rank, crowd);
        u = rand(1, dims);
        beta = ((2 * u) .^ (1/3)) .* (u <= 0.5) + ((1 ./ (2 * (1 - u))) .^ (1/3)) .* (u > 0.5);
        c1 = 0.5 * ((1 + beta) .* pop(a1, :) + (1 - beta) .* pop(a2, :));
        c2 = 0.5 * ((1 - beta) .* pop(a1, :) + (1 + beta) .* pop(a2, :));
        mut1 = rand(1, dims) < 0.1; c1(mut1) = c1(mut1) + 0.1 * randn(1, sum(mut1));
        mut2 = rand(1, dims) < 0.1; c2(mut2) = c2(mut2) + 0.1 * randn(1, sum(mut2));
        children(k, :) = min(max(c1, low), high);
        if k + 1 <= popSize
            children(k + 1, :) = min(max(c2, low), high);
        end
    end
    merged = [pop; children];
    mergedObj = obj(merged);
    [mf, ~] = ndsort(mergedObj);
    newPop = []; newObj = [];
    for f = 1:numel(mf)
        idx = mf{f};
        if size(newPop, 1) + numel(idx) <= popSize
            newPop = [newPop; merged(idx, :)]; %#ok<AGROW>
            newObj = [newObj; mergedObj(idx, :)]; %#ok<AGROW>
        else
            d = crowdDist(mergedObj, idx);
            [~, order] = sort(d, 'descend');
            take = idx(order(1:popSize - size(newPop, 1)));
            newPop = [newPop; merged(take, :)]; %#ok<AGROW>
            newObj = [newObj; mergedObj(take, :)]; %#ok<AGROW>
            break
        end
    end
    pop = newPop; objs = newObj;
end

[fronts, ~] = ndsort(objs);
front = fronts{1};
T = table(objs(front, 1), objs(front, 2), 'VariableNames', {'f1', 'f2'});
mmlib_report('NSGA-II', sprintf('Pareto解个数=%d', numel(front)), ...
    sprintf('f1范围=%.3f~%.3f', min(objs(front, 1)), max(objs(front, 1))), ...
    sprintf('f2范围=%.3f~%.3f', min(objs(front, 2)), max(objs(front, 2))));
mmlib_savetable(here, 'nsga2', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）

function pick = tournament(rank, crowd)
i = randi(numel(rank)); j = randi(numel(rank));
if rank(i) ~= rank(j)
    if rank(i) < rank(j), pick = i; else, pick = j; end
else
    if crowd(i) >= crowd(j), pick = i; else, pick = j; end
end
end

function [fronts, rank] = ndsort(objs)
n = size(objs, 1);
domBy = cell(n, 1); count = zeros(n, 1);
for p = 1:n
    for q = 1:n
        if p == q, continue; end
        if all(objs(p, :) <= objs(q, :)) && any(objs(p, :) < objs(q, :))
            domBy{p} = [domBy{p} q];
        elseif all(objs(q, :) <= objs(p, :)) && any(objs(q, :) < objs(p, :))
            count(p) = count(p) + 1;
        end
    end
end
fronts = cell(n, 1); levels = 0; current = find(count == 0)';
while ~isempty(current)
    levels = levels + 1;
    fronts{levels} = current;
    nxt = [];
    for p = current
        for q = domBy{p}
            count(q) = count(q) - 1;
            if count(q) == 0
                nxt = [nxt q]; %#ok<AGROW>
            end
        end
    end
    current = nxt;
end
fronts = fronts(1:levels);
rank = zeros(n, 1);
for k = 1:numel(fronts)
    rank(fronts{k}) = k;
end
end

function d = crowdDist(objs, front)
m = numel(front); d = zeros(m, 1);
if m <= 2
    d(:) = inf; return
end
vals = objs(front, :);
for k = 1:size(vals, 2)
    [~, order] = sort(vals(:, k));
    d(order(1)) = inf; d(order(end)) = inf;
    span = vals(order(end), k) - vals(order(1), k);
    if span > 0
        for i = 2:m - 1
            d(order(i)) = d(order(i)) + (vals(order(i + 1), k) - vals(order(i - 1), k)) / span;
        end
    end
end
end
