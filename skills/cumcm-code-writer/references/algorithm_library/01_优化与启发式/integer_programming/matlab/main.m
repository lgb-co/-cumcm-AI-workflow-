% 整数规划 · 小规模整数资源分配（MATLAB 最小可运行模板）
% 模型：max 5 x1 + 4 x2, s.t. 6x1+4x2<=24, x1+2x2<=6, x 非负整数
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

c = [5; 4];
A = [6 4; 1 2];
b = [24; 6];

options = optimoptions('intlinprog', 'Display', 'off');
[x, fval, exitflag] = intlinprog(-c, [1 2], A, b, [], [], zeros(2, 1), [], options);
if exitflag <= 0
    error('整数规划未收敛：exitflag=%d', exitflag);
end

mmlib_report('整数规划', sprintf('x1=%d', round(x(1))), sprintf('x2=%d', round(x(2))), sprintf('最优值=%.4f', -fval));
T = table(["x1"; "x2"], round(x, 4), 'VariableNames', {'变量', '取值'});
mmlib_savetable(here, 'integer_programming', T);
