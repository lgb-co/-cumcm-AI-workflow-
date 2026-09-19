% 普通克里金插值（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
points = 10 * rand(24, 2);
values = sin(points(:, 1) / 2) + cos(points(:, 2) / 3) + 0.1 * randn(24, 1);
axisVec = linspace(0, 10, 40);
[gx, gy] = meshgrid(axisVec, axisVec);
gridPoints = [gx(:) gy(:)];

D = squareform(pdist(points));
n = size(points, 1);
bestResidual = inf;
for nugget = [0 0.01 0.05]
    for sill = linspace(0.05, 3, 12)
        for rang = linspace(0.5, 5, 10)
            gamma = nugget + sill * (1 - exp(-D / rang));
            target = nugget + sill * (1 - exp(-mean(D(D > 0)) / rang));
            residual = sum(sum((gamma - target).^2));
            if residual < bestResidual
                bestResidual = residual; best = [nugget sill rang];
            end
        end
    end
end
nugget = best(1); sill = best(2); rang = best(3);

Gamma = nugget + sill * (1 - exp(-D / rang));
A = [Gamma ones(n, 1); ones(1, n) 0];
predictions = zeros(size(gridPoints, 1), 1);
variances = zeros(size(gridPoints, 1), 1);
for k = 1:size(gridPoints, 1)
    d = sqrt(sum((points - gridPoints(k, :)).^2, 2));
    b = [nugget + sill * (1 - exp(-d / rang)); 1];
    sol = A \ b;
    predictions(k) = sol(1:n)' * values;
    variances(k) = sol(1:n)' * b(1:n) + sol(n + 1);
end

mmlib_report('普通克里金', sprintf('c0=%.3f c=%.3f a=%.3f', nugget, sill, rang), ...
    sprintf('预测范围=%.3f~%.3f', min(predictions), max(predictions)), ...
    sprintf('平均克里金方差=%.5f', mean(variances)));
T = table(predictions, variances, 'VariableNames', {'预测值', '克里金方差'});
mmlib_savetable(here, 'kriging', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
