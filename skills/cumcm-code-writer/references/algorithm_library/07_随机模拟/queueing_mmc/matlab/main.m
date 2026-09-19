% M/M/c 多服务台排队模型（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

lam = 8; mu = 3; c = 4;
rho = lam / (c * mu);
assert(rho < 1, '系统不稳定：rho>=1');
a = lam / mu;
p0 = 1 / (sum(a.^(0:c-1) ./ factorial(0:c-1)) + a^c / (factorial(c) * (1 - rho)));
C = a^c / (factorial(c) * (1 - rho)) * p0;
Lq = C * rho / (1 - rho);
Wq = Lq / lam;
W = Wq + 1 / mu;

mmlib_report('M/M/c', sprintf('到达率=%.1f', lam), sprintf('服务率=%.1f', mu), ...
    sprintf('服务台=%d', c), sprintf('利用率=%.4f', rho), sprintf('平均等待=%.4f', Wq));
T = table(["rho"; "C"; "P0"; "L"; "Lq"; "W"; "Wq"], [rho; C; p0; Lq + a; Lq; W; Wq], ...
    'VariableNames', {'指标', '数值'});
mmlib_savetable(here, 'queueing_mmc', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
