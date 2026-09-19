% 演化博弈 · 复制动态（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

A = [3.0 1.0 2.5; 4.0 2.0 1.0; 3.2 1.5 2.2];
names = ["合作", "搭便车", "惩罚"];
starts = [0.8 0.1 0.1; 0.1 0.8 0.1; 0.1 0.1 0.8; 0.34 0.33 0.33];
tEnd = 60;

rhs = @(t, x) x .* ((A * x) - (x' * A * x));
trajectories = cell(size(starts, 1), 1);
finals = zeros(size(starts));
for k = 1:size(starts, 1)
    [t, y] = ode45(rhs, linspace(0, tEnd, 301), starts(k, :)');
    trajectories{k} = struct('t', t, 'y', y);
    finals(k, :) = y(end, :)';
end

mmlib_report('演化博弈', sprintf('轨迹数=%d', size(starts, 1)), ...
    sprintf('平均末态占比=%s', mat2str(round(mean(finals, 1), 4))), ...
    sprintf('占优策略=%s', names(find(mean(finals, 1) == max(mean(finals, 1)), 1))));
T = table(string(1:size(starts, 1))', finals(:, 1), finals(:, 2), finals(:, 3), ...
    'VariableNames', {'初始编号', '合作占比', '搭便车占比', '惩罚占比'});
mmlib_savetable(here, 'evolutionary_game', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
