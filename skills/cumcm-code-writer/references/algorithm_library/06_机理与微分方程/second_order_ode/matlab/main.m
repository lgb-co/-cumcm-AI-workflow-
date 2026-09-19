% 二阶微分方程 · 阻尼振动（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

zeta = 0.08; omega = 2.0; tEnd = 20;
rhs = @(t, y) [y(2); -2*zeta*omega*y(2) - omega^2*y(1)];

[t, y] = ode45(rhs, linspace(0, tEnd, 2001), [1; 0]);
idxPeak = find(y(2:end-1, 1) > y(1:end-2, 1) & y(2:end-1, 1) > y(3:end, 1)) + 1;
locs = t(idxPeak);
period = mean(diff(locs));

mmlib_report('阻尼振动', sprintf('阻尼比=%.2f', zeta), sprintf('固有频率=%.2f', omega), ...
    sprintf('周期=%.4f', period), sprintf('末态位移=%.5f', y(end, 1)));
T = table(t, y(:, 1), y(:, 2), 'VariableNames', {'时间', '位移x', '速度v'});
mmlib_savetable(here, 'second_order_ode', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
