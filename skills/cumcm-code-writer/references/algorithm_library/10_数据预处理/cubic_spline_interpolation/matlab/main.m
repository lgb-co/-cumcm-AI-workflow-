% 三次样条插值（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

xNodes = linspace(0, 10, 11);
yNodes = sin(xNodes) + 0.1 * xNodes;
xQuery = linspace(0, 10, 201);

splineValues = spline(xNodes, yNodes, xQuery);
polyValues = polyval(polyfit(xNodes, yNodes, numel(xNodes) - 1), xQuery);
trueValues = sin(xQuery) + 0.1 * xQuery;

mmlib_report('三次样条插值', sprintf('节点数=%d', numel(xNodes)), ...
    sprintf('样条最大误差=%.3e', max(abs(splineValues - trueValues))), ...
    sprintf('高次多项式最大误差=%.3e', max(abs(polyValues - trueValues))));
T = table(xQuery', trueValues', splineValues', polyValues', ...
    'VariableNames', {'x', '真值', '三次样条', '高次多项式'});
mmlib_savetable(here, 'cubic_spline_interpolation', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
