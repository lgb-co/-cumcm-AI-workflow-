% 一维热传导方程 · 显式有限差分（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

L = 1; nx = 51; a = 0.01; tEnd = 5; uL = 100; uR = 0;
dx = L / (nx - 1);
dt = 0.4 * dx^2 / a;
steps = ceil(tEnd / dt);
dt = tEnd / steps;
r = a * dt / dx^2;
assert(r <= 0.5, '显式格式不稳定：r=%.3f', r);

u = zeros(nx, 1); u(1) = uL; u(end) = uR;
history = zeros(nx, steps + 1); history(:, 1) = u;
for k = 1:steps
    uNext = u;
    uNext(2:end-1) = u(2:end-1) + r * (u(3:end) - 2*u(2:end-1) + u(1:end-2));
    uNext(1) = uL; uNext(end) = uR;
    u = uNext;
    history(:, k + 1) = u;
end
x = linspace(0, L, nx)';

mmlib_report('热传导方程', sprintf('网格数=%d', nx), sprintf('r=%.4f', r), sprintf('时间步数=%d', steps));
T = table(x, history(:, 1), history(:, round(steps/4)), history(:, end), ...
    'VariableNames', {'x', '初始', '中期', '终态'});
mmlib_savetable(here, 'heat_equation_1d', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
