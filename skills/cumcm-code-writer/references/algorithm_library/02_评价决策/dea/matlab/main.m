% DEA · CCR 模型效率评价（MATLAB 最小可运行模板）
% 线性形式：min -u'*Y(j,:)'，s.t. v'*X(j,:)'=1，u'*Y' - v'*X' <= 0，u,v >= 0
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

X = [20 30; 25 28; 30 35; 22 26; 28 32];
Y = [60 40; 55 45; 70 42; 58 38; 65 48];
n = size(X, 1); m = size(X, 2); s = size(Y, 2);
eff = zeros(n, 1);
options = optimoptions('linprog', 'Display', 'off');

for j = 1:n
    c = [zeros(1, m) -Y(j, :)];
    A = [-X Y];
    b = zeros(n, 1);
    Aeq = [X(j, :) zeros(1, s)];
    beq = 1;
    [~, fval] = linprog(c, A, b, Aeq, beq, zeros(m + s, 1), [], options);
    eff(j) = -fval;
end

mmlib_report('DEA-CCR', sprintf('效率值=%s', mat2str(round(eff', 4))), ...
    sprintf('有效单元=%d', sum(eff > 0.999)));
T = table("DMU" + string(1:n)', eff, 'VariableNames', {'决策单元', '综合效率'});
mmlib_savetable(here, 'dea', T);
