% 系统动力学（存量-流量）简化模型（MATLAB 最小可运行模板）
% 存量：人口 P、资源存量 R；流量：出生/死亡、再生/消耗；欧拉法逐步积分。
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

P = 100; R = 1000; b = 0.08; d = 0.03; regen = 60; consume = 0.6; capacity = 400;
tEnd = 120; dt = 0.1;
steps = round(tEnd / dt);
t = (0:steps)' * dt;
population = zeros(steps + 1, 1); resource = zeros(steps + 1, 1);
population(1) = P; resource(1) = R;

for k = 1:steps
    crowding = min(1, P / capacity);
    scarcity = max(0, 1 - (R / max(P, 1e-9)) / 10);
    births = b * P * (1 - crowding);
    deaths = d * P * (1 + scarcity);
    regeneration = regen * (1 - R / (capacity * 10));
    consumption = consume * P;
    P = max(0, P + (births - deaths) * dt);
    R = max(0, R + (regeneration - consumption) * dt);
    population(k + 1) = P; resource(k + 1) = R;
end

[peak, idx] = max(population);
change = (population(end) - population(round(steps * 0.8))) / max(population(round(steps * 0.8)), 1e-9);

mmlib_report('系统动力学', sprintf('人口峰值=%.2f', peak), sprintf('达峰时间=%.2f', t(idx)), ...
    sprintf('末期人口=%.2f', population(end)), sprintf('末期资源=%.2f', resource(end)), ...
    sprintf('末段变化率=%.4f', change));
T = table(t, population, resource, resource ./ max(population, 1e-9), ...
    'VariableNames', {'时间', '人口P', '资源R', '人均资源'});
mmlib_savetable(here, 'system_dynamics', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
