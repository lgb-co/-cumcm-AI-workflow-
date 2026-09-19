% 非线性规划 · 带不等式约束的连续优化（MATLAB 最小可运行模板）
% 模型：min (x1-1)^2+(x2-2.5)^2, s.t. x1-2x2+2>=0, -x1-2x2+6>=0, -x1+2x2+2>=0, x>=0
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

obj = @(x) (x(1) - 1).^2 + (x(2) - 2.5).^2;
cons = @(x) deal([], [x(1) - 2*x(2) + 2; -x(1) - 2*x(2) + 6; -x(1) + 2*x(2) + 2]);
options = optimoptions('fmincon', 'Display', 'off', 'Algorithm', 'sqp');

bestX = []; bestF = inf;
rng(42);
starts = [0.5 0.5; rand(11, 2) .* 4];
for k = 1:size(starts, 1)
    [x, f] = fmincon(obj, starts(k, :)', [], [], [], [], [0; 0], [], cons, options);
    if f < bestF
        bestX = x; bestF = f;
    end
end

g = [bestX(1) - 2*bestX(2) + 2; -bestX(1) - 2*bestX(2) + 6; -bestX(1) + 2*bestX(2) + 2];
mmlib_report('非线性规划', sprintf('x1=%.4f', bestX(1)), sprintf('x2=%.4f', bestX(2)), ...
    sprintf('最优值=%.6f', bestF), sprintf('约束余量=%.6f', min(g)));
T = table(["x1"; "x2"], round(bestX, 6), 'VariableNames', {'变量', '取值'});
mmlib_savetable(here, 'nonlinear_programming', T);
