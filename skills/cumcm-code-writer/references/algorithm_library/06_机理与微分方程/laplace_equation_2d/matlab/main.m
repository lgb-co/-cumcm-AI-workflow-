% 二维拉普拉斯方程 · SOR 迭代（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

nx = 61; ny = 61; omega = 1.7; tol = 1e-6; maxIter = 20000;
u = zeros(ny, nx);
u(1, :) = 100; u(end, :) = 100;

iterations = maxIter; residual = inf;
for k = 1:maxIter
    residual = 0;
    for j = 2:ny-1
        for i = 2:nx-1
            old = u(j, i);
            uNew = 0.25 * (u(j - 1, i) + u(j + 1, i) + u(j, i - 1) + u(j, i + 1));
            u(j, i) = old + omega * (uNew - old);
            residual = max(residual, abs(u(j, i) - old));
        end
        u(j, 1) = 0; u(j, end) = 0;
    end
    if residual < tol
        iterations = k; break
    end
end

mmlib_report('拉普拉斯方程', sprintf('网格=%dx%d', nx, ny), sprintf('松弛因子=%.1f', omega), ...
    sprintf('迭代次数=%d', iterations), sprintf('末次残差=%.2e', residual), ...
    sprintf('中心温度=%.3f', u(round(ny/2), round(nx/2))));
x = linspace(0, 1, nx)'; y = linspace(0, 1, ny)';
T = table(y, u(:, round(nx/2)), 'VariableNames', {'y', 'u_mid'});
mmlib_savetable(here, 'laplace_equation_2d', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
