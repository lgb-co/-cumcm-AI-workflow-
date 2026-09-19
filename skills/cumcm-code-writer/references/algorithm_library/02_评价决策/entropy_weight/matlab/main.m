% 熵权法 · 客观赋权（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

X = [92 0.83 3.1 8; 78 0.71 4.5 6; 85 0.90 2.7 9; 70 0.64 5.2 5; 88 0.79 3.6 7];
positive = [true true false true];

Z = zeros(size(X));
for j = 1:size(X, 2)
    col = X(:, j);
    if positive(j)
        Z(:, j) = (col - min(col)) / (max(col) - min(col));
    else
        Z(:, j) = (max(col) - col) / (max(col) - min(col));
    end
end
Z = Z + 0.002;
P = Z ./ sum(Z, 1);
n = size(Z, 1);
E = -sum(P .* log(P), 1) / log(n);
d = 1 - E;
w = d / sum(d);

mmlib_report('熵权法', sprintf('权重=%s', mat2str(round(w, 4))), sprintf('熵值=%s', mat2str(round(E, 4))));
T = table("X" + string(1:numel(w))', E', w', 'VariableNames', {'指标', '熵值', '权重'});
mmlib_savetable(here, 'entropy_weight', T);
