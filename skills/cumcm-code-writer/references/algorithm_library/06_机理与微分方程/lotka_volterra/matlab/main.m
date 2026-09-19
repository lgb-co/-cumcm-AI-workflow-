% Lotka-Volterra 捕食者-被捕食者模型（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

alpha = 1.1; beta = 0.4; delta = 0.1; gamma = 0.4; tEnd = 60;
rhs = @(t, y) [alpha*y(1) - beta*y(1)*y(2); delta*y(1)*y(2) - gamma*y(2)];

[t, y] = ode45(rhs, linspace(0, tEnd, 1201), [10; 5]);
idxPeak = find(y(2:end-1, 1) > y(1:end-2, 1) & y(2:end-1, 1) > y(3:end, 1)) + 1;
locs = t(idxPeak);
period = mean(diff(locs));

mmlib_report('Lotka-Volterra', sprintf('周期=%.3f', period), ...
    sprintf('被捕食者峰值=%.2f', max(y(:, 1))), sprintf('捕食者峰值=%.2f', max(y(:, 2))));
T = table(t, y(:, 1), y(:, 2), 'VariableNames', {'时间', '被捕食者x', '捕食者y'});
mmlib_savetable(here, 'lotka_volterra', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
