% Shapley 值 · 合作博弈收益分配（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

n = 3;
names = ["城市A", "城市B", "城市C"];
keys = {[1], [2], [3], [1 2], [1 3], [2 3], [1 2 3]};
costs = [100 120 90 170 150 165 200];

value = @(subset) cost_of(subset, keys, costs);
phi = zeros(1, n);
for player = 1:n
    others = setdiff(1:n, player);
    for subsetSize = 0:numel(others)
        combos = nchoosek(others, subsetSize);
        if subsetSize == 0, combos = []; end
        for r = 1:size(combos, 1)
            subset = combos(r, :);
            weight = factorial(subsetSize) * factorial(n - subsetSize - 1) / factorial(n);
            phi(player) = phi(player) + weight * (value([subset player]) - value(subset));
        end
        if subsetSize == 0 && isempty(combos)
            weight = factorial(0) * factorial(n - 1) / factorial(n);
            phi(player) = phi(player) + weight * (value(player) - value([]));
        end
    end
end

mmlib_report('Shapley 值', sprintf('分配=%s', mat2str(round(phi, 4))), ...
    sprintf('分配合计=%.4f', sum(phi)), sprintf('大联盟成本=%.4f', costs(end)));
T = table(names', phi', 'VariableNames', {'成员', '分摊成本'});
mmlib_savetable(here, 'shapley_value', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）

function v = cost_of(subset, keys, costs)
if isempty(subset), v = 0; return; end
subset = sort(subset(:))';
for k = 1:numel(keys)
    if isequal(sort(keys{k}), subset)
        v = costs(k); return
    end
end
v = 0;
end
