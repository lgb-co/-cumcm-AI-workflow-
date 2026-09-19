% 灰色关联分析 · 因素影响排序（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

X = [2.1 1.2 4.5 3.0; 3.4 2.0 4.9 3.8; 5.2 3.1 5.6 4.9;
     7.8 4.4 6.8 6.5; 9.1 5.0 7.1 7.4; 11.3 6.2 7.9 8.8];
y = [10.5 12.0 13.4 15.9 17.2 19.6]';
rho = 0.5;

scale = @(v) (v - min(v)) / (max(v) - min(v));
Y = scale(y);
F = zeros(size(X));
for j = 1:size(X, 2)
    F(:, j) = scale(X(:, j));
end
D = abs(Y - F);
dmin = min(D(:)); dmax = max(D(:));
coef = (dmin + rho * dmax) ./ (D + rho * dmax);
degree = mean(coef, 1);
[~, order] = sort(degree, 'descend');

mmlib_report('灰色关联', sprintf('关联度=%s', mat2str(round(degree, 4))), sprintf('排序=%s', mat2str(order)));
T = table("X" + string(1:numel(degree))', degree', 'VariableNames', {'因素', '关联度'});
mmlib_savetable(here, 'grey_relational', T);
