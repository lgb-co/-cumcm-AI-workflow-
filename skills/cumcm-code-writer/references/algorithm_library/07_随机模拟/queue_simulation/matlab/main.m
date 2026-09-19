% 排队系统蒙特卡洛仿真（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
lam = 2.4; mu = 3.0; n = 5000; warmup = 500;
arrivals = cumsum(exprnd(1/lam, n, 1));
service = exprnd(1/mu, n, 1);
start = zeros(n, 1); finish = zeros(n, 1);
for i = 1:n
    prev = 0; if i > 1, prev = finish(i - 1); end
    start(i) = max(arrivals(i), prev);
    finish(i) = start(i) + service(i);
end
wait = start - arrivals;
utilization = sum(service) / finish(end);

mmlib_report('排队仿真', sprintf('平均等待=%.4f', mean(wait(warmup+1:end))), ...
    sprintf('理论等待=%.4f', 1/(mu - lam)), sprintf('利用率=%.4f', utilization), ...
    sprintf('顾客数=%d', n));
T = table((1:200)', wait(1:200), 'VariableNames', {'顾客', '等待时间'});
mmlib_savetable(here, 'queue_simulation', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
