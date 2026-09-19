% SIR 传染病模型（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

N = 10000; I0 = 10; beta = 0.35; gamma = 0.12; days = 120;
rhs = @(t, y) [-beta*y(1)*y(2)/N; beta*y(1)*y(2)/N - gamma*y(2); gamma*y(2)];

[t, y] = ode45(rhs, 0:1:days, [N - I0; I0; 0]);
[peak, idx] = max(y(:, 2));
peakTime = t(idx);
R0 = beta / gamma;

mmlib_report('SIR 模型', sprintf('R0=%.3f', R0), sprintf('感染峰值=%.1f', peak), ...
    sprintf('达峰时间=%.1f', peakTime), sprintf('最终累计感染=%.1f', y(end, 3)));
T = table(t, y(:, 1), y(:, 2), y(:, 3), 'VariableNames', {'天', 'S', 'I', 'R'});
mmlib_savetable(here, 'sir_model', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
