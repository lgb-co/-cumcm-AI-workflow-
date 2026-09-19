% 线性规划 · 生产资源分配（MATLAB 最小可运行模板）
% 模型：max 50 x1 + 30 x2, s.t. 4x1+3x2<=120, 2x1+x2<=50, x>=0
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

c = [50; 30];
A = [4 3; 2 1];
b = [120; 50];
lb = [0; 0];

options = optimoptions('linprog', 'Display', 'off');
[x, fval, exitflag] = linprog(-c, A, b, [], [], lb, [], options);
if exitflag <= 0
    error('线性规划未收敛：exitflag=%d', exitflag);
end

mmlib_report('线性规划', sprintf('x1=%.4f', x(1)), sprintf('x2=%.4f', x(2)), sprintf('最优值=%.4f', -fval));
T = table(["x1"; "x2"], round(x, 4), 'VariableNames', {'变量', '取值'});
mmlib_savetable(here, 'linear_programming', T);
