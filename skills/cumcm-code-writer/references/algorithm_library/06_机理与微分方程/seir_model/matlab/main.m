% SEIR 传染病模型（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

N = 10000; E0 = 20; I0 = 5; beta = 0.45; sigma = 0.2; gamma = 0.15; days = 180;
rhs = @(t, y) [-beta*y(1)*y(3)/N; beta*y(1)*y(3)/N - sigma*y(2); sigma*y(2) - gamma*y(3); gamma*y(3)];

[t, y] = ode45(rhs, 0:1:days, [N - E0 - I0; E0; I0; 0]);
[peak, idx] = max(y(:, 3));

mmlib_report('SEIR 模型', sprintf('R0=%.3f', beta / gamma), sprintf('感染峰值=%.1f', peak), ...
    sprintf('达峰时间=%.1f', t(idx)), sprintf('最终累计感染=%.1f', y(end, 4)));
T = table(t, y(:, 1), y(:, 2), y(:, 3), y(:, 4), 'VariableNames', {'天', 'S', 'E', 'I', 'R'});
mmlib_savetable(here, 'seir_model', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
