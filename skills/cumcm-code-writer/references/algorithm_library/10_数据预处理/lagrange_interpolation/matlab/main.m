% 拉格朗日插值（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

xNodes = linspace(0, 10, 7);
yNodes = sin(xNodes) + 0.1 * xNodes;
xQuery = linspace(0, 10, 101);

values = zeros(size(xQuery));
for q = 1:numel(xQuery)
    total = 0;
    for i = 1:numel(xNodes)
        basis = 1;
        for j = 1:numel(xNodes)
            if i ~= j
                basis = basis * (xQuery(q) - xNodes(j)) / (xNodes(i) - xNodes(j));
            end
        end
        total = total + basis * yNodes(i);
    end
    values(q) = total;
end
dense = sin(xQuery) + 0.1 * xQuery;

mmlib_report('拉格朗日插值', sprintf('节点数=%d', numel(xNodes)), ...
    sprintf('最大误差=%.3e', max(abs(values - dense))));
T = table(xQuery', values', dense', 'VariableNames', {'x', '插值值', '真值'});
mmlib_savetable(here, 'lagrange_interpolation', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
