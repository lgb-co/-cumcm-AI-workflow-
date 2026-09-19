% TOPSIS · 逼近理想解排序（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

X = [92 0.83 3.1 8; 78 0.71 4.5 6; 85 0.90 2.7 9; 70 0.64 5.2 5; 88 0.79 3.6 7];
w = [0.25 0.35 0.20 0.20];
positive = [true true false true];

Z = X ./ sqrt(sum(X.^2, 1));
V = Z .* w;
bestV = zeros(1, size(X, 2)); worstV = bestV;
for j = 1:size(X, 2)
    if positive(j)
        bestV(j) = max(V(:, j)); worstV(j) = min(V(:, j));
    else
        bestV(j) = min(V(:, j)); worstV(j) = max(V(:, j));
    end
end
dB = sqrt(sum((V - bestV).^2, 2));
dW = sqrt(sum((V - worstV).^2, 2));
C = dW ./ (dB + dW);
[~, order] = sort(C, 'descend');
rank = zeros(size(C)); rank(order) = 1:numel(C);

mmlib_report('TOPSIS', sprintf('贴近度=%s', mat2str(round(C', 4))), sprintf('排名=%s', mat2str(rank')));
T = table("A" + string(1:numel(C))', C, rank, 'VariableNames', {'方案', '贴近度', '排名'});
mmlib_savetable(here, 'topsis', T);
