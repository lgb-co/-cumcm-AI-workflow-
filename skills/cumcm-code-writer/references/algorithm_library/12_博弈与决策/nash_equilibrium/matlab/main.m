% 纳什均衡求解 · 双人矩阵博弈（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

A = [3 0; 5 1];      % 行玩家收益
B = [3 5; 0 1];      % 列玩家收益
rowNames = ["合作", "背叛"]; colNames = ["合作", "背叛"];

pure = {};
for i = 1:2
    for j = 1:2
        if A(i, j) >= max(A(:, j)) - 1e-12 && B(i, j) >= max(B(i, :)) - 1e-12
            pure{end + 1} = sprintf('(%s, %s)', rowNames(i), colNames(j)); %#ok<AGROW>
        end
    end
end

denomP = A(1, 1) - A(1, 2) - A(2, 1) + A(2, 2);
denomQ = B(1, 1) - B(2, 1) - B(1, 2) + B(2, 2);
mixedText = '无';
if abs(denomP) > 1e-12 && abs(denomQ) > 1e-12
    p = (A(2, 2) - A(1, 2)) / denomP;
    q = (B(2, 2) - B(2, 1)) / denomQ;
    if p >= 0 && p <= 1 && q >= 0 && q <= 1
        mixedText = sprintf('行玩家 p=%.3f，列玩家 q=%.3f', p, q);
    end
end

mmlib_report('纳什均衡', sprintf('纯策略均衡=%s', strjoin(pure, '; ')), sprintf('混合均衡=%s', mixedText));
rowIdx = [1; 1; 2; 2]; colIdx = [1; 2; 1; 2];
T = table(rowNames(rowIdx)', colNames(colIdx)', A(:), B(:), ...
    'VariableNames', {'行策略', '列策略', '行收益', '列收益'});
mmlib_savetable(here, 'nash_equilibrium', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
