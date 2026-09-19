% 一维波动方程 · 显式有限差分（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

L = 1; nx = 101; c = 1; tEnd = 1;
dx = L / (nx - 1);
dt = 0.8 * dx / c;
steps = ceil(tEnd / dt);
dt = tEnd / steps;
r2 = (c * dt / dx)^2;
assert(r2 <= 1, 'CFL 条件不满足：r2=%.3f', r2);

x = linspace(0, L, nx)';
u = sin(3 * pi * x) .* exp(-40 * (x - 0.5).^2);
u(1) = 0; u(end) = 0;
uPrev = u;
energy = zeros(steps + 1, 1);
energy(1) = sum(u(2:end-1).^2) * dx;
snapshots = zeros(nx, 5);
snapshots(:, 1) = u;
marks = zeros(1, 5);
interval = max(1, floor(steps / 4));
count = 1;

for k = 1:steps
    uNext = zeros(nx, 1);
    uNext(2:end-1) = 2*u(2:end-1) - uPrev(2:end-1) + r2 * (u(3:end) - 2*u(2:end-1) + u(1:end-2));
    uPrev = u; u = uNext;
    energy(k + 1) = sum(u(2:end-1).^2) * dx;
    if mod(k, interval) == 0 && count < 5
        count = count + 1;
        snapshots(:, count) = u;
        marks(count) = k * dt;
    end
end

mmlib_report('波动方程', sprintf('网格数=%d', nx), sprintf('CFL平方=%.4f', r2), ...
    sprintf('能量漂移=%.6f', abs(energy(end) - energy(1)) / energy(1)));
T = table(x, snapshots(:, 1), snapshots(:, 2), snapshots(:, 3), snapshots(:, 4), snapshots(:, 5), ...
    'VariableNames', {'x', 't1', 't2', 't3', 't4', 't5'});
mmlib_savetable(here, 'wave_equation_1d', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
