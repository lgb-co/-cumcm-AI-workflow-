% 遗传算法 · 连续函数寻优（MATLAB 最小可运行模板）
% 模型：max 21.5 + x*sin(4*pi*x) + y*sin(20*pi*y)，x∈[-3,12.1]，y∈[4.1,5.8]
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

low = [-3, 4.1]; high = [12.1, 5.8];
fit = @(P) 21.5 + P(:, 1) .* sin(4*pi*P(:, 1)) + P(:, 2) .* sin(20*pi*P(:, 2));
rng(42);
popSize = 60; generations = 100;
pop = low + rand(popSize, 2) .* (high - low);
val = fit(pop);
history = zeros(generations, 1);

for g = 1:generations
    [~, idx] = max(val);
    elite = pop(idx, :); eliteVal = val(idx);
    children = elite;
    while size(children, 1) < popSize - 1
        pool = randperm(popSize, 2);
        alpha = rand();
        child = alpha * pop(pool(1), :) + (1 - alpha) * pop(pool(2), :);
        if rand() < 0.3
            child = child + 0.1 * (high - low) .* randn(1, 2);
        end
        children(end + 1, :) = min(max(child, low), high); %#ok<AGROW>
    end
    pop = [elite; children];
    val = fit(pop);
    history(g) = max(val);
end

[bestVal, idx] = max(val);
mmlib_report('遗传算法', sprintf('迭代=%d', generations), sprintf('最优x=%.4f', pop(idx, 1)), ...
    sprintf('最优y=%.4f', pop(idx, 2)), sprintf('最优值=%.4f', bestVal));
mmlib_savetable(here, 'genetic_algorithm', table((1:generations)', history, 'VariableNames', {'代数', '最优值'}));

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
