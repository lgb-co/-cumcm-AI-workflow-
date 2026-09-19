% 动态规划 · 0-1 背包（MATLAB 最小可运行模板）
% 状态：dp(j+1) 表示容量 j 下的最大价值；容量倒序遍历保证每件物品只取一次。
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

weights = [2 3 4 5 9];
values = [3 4 5 8 10];
capacity = 20;
n = numel(weights);

dp = zeros(1, capacity + 1);
choice = false(n, capacity + 1);
for i = 1:n
    for j = capacity:-1:weights(i)
        if dp(j - weights(i) + 1) + values(i) > dp(j + 1)
            dp(j + 1) = dp(j - weights(i) + 1) + values(i);
            choice(i, j + 1) = true;
        end
    end
end

picked = [];
remaining = capacity;
for i = n:-1:1
    if choice(i, remaining + 1)
        picked = [i picked]; %#ok<AGROW>
        remaining = remaining - weights(i);
    end
end

mmlib_report('0-1 背包', sprintf('最大价值=%d', dp(capacity + 1)), ...
    sprintf('选中物品=%s', mat2str(picked)), sprintf('总重量=%d', sum(weights(picked))), ...
    sprintf('容量=%d', capacity));
T = table((1:n)', weights', values', ismember(1:n, picked)', ...
    'VariableNames', {'物品', '重量', '价值', '是否选中'});
mmlib_savetable(here, 'dynamic_programming_knapsack', T);