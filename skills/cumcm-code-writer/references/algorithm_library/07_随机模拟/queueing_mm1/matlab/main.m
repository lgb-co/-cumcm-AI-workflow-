% M/M/1 排队论解析公式（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

lam = 2.4; mu = 3.0;
rho = lam / mu;
assert(rho < 1, '系统不稳定：rho>=1');

L = rho / (1 - rho); Lq = rho^2 / (1 - rho);
W = 1 / (mu - lam); Wq = rho / (mu - lam); P0 = 1 - rho;

mmlib_report('M/M/1', sprintf('利用率=%.4f', rho), sprintf('平均队长=%.4f', L), ...
    sprintf('平均等待=%.4f', Wq), sprintf('空闲概率=%.4f', P0));
T = table(["rho"; "L"; "Lq"; "W"; "Wq"; "P0"], [rho; L; Lq; W; Wq; P0], ...
    'VariableNames', {'指标', '数值'});
mmlib_savetable(here, 'queueing_mm1', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
