% 粒子群优化 PSO · Rosenbrock 函数寻优（MATLAB 最小可运行模板）
% 模型：min 100(y-x^2)^2 + (1-x)^2，最优解 (1,1)，最优值 0
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

bound = 2.5;
fit = @(P) 100 .* (P(:, 2) - P(:, 1).^2).^2 + (1 - P(:, 1)).^2;
rng(42);
n = 30; iterations = 200;
pos = -bound + 2 * bound * rand(n, 2);
vel = 0.2 * (rand(n, 2) - 0.5);
pbest = pos; pbestVal = fit(pos);
[gbestVal, idx] = min(pbestVal);
gbest = pbest(idx, :);
history = zeros(iterations, 1);

for it = 1:iterations
    w = 0.9 - 0.5 * it / iterations;
    vel = w * vel + 1.5 * rand(n, 2) .* (pbest - pos) + 1.5 * rand(n, 2) .* (gbest - pos);
    pos = min(max(pos + vel, -bound), bound);
    val = fit(pos);
    better = val < pbestVal;
    pbest(better, :) = pos(better, :);
    pbestVal(better) = val(better);
    [curBest, idx] = min(pbestVal);
    if curBest < gbestVal
        gbestVal = curBest; gbest = pbest(idx, :);
    end
    history(it) = gbestVal;
end

mmlib_report('粒子群', sprintf('最优x=%.4f', gbest(1)), sprintf('最优y=%.4f', gbest(2)), ...
    sprintf('最优值=%.3e', gbestVal));
mmlib_savetable(here, 'particle_swarm', table((1:iterations)', history, 'VariableNames', {'迭代', '全局最优'}));

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
