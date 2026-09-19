% Lorenz 混沌系统（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

sigma = 10; rho = 28; beta = 8/3; tEnd = 30; perturb = 1e-8;
rhs = @(t, y) [sigma*(y(2) - y(1)); y(1)*(rho - y(3)) - y(2); y(1)*y(2) - beta*y(3)];

[t, base] = ode45(rhs, linspace(0, tEnd, 6001), [1; 1; 1]);
[~, shifted] = ode45(rhs, linspace(0, tEnd, 6001), [1 + perturb; 1; 1]);
distance = sqrt(sum((base - shifted).^2, 2));
crossIdx = find(distance > 1, 1);

mmlib_report('Lorenz 系统', sprintf('初值扰动=%.0e', perturb), ...
    sprintf('末态距离=%.4g', distance(end)), ...
    sprintf('分离时刻=%.2f', ternary(isempty(crossIdx), NaN, t(crossIdx))));
T = table(t, base(:, 1), base(:, 2), base(:, 3), distance, ...
    'VariableNames', {'时间', 'x', 'y', 'z', '初值间距离'});
mmlib_savetable(here, 'lorenz_system', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）

function out = ternary(cond, a, b)
if cond, out = a; else, out = b; end
end
