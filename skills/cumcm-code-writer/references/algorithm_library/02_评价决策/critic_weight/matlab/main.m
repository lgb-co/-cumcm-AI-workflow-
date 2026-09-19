% CRITIC 客观赋权法（MATLAB 最小可运行模板）
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
sd = std(Z, 0, 1);
corrMat = corr(Z);
conflict = sum(1 - corrMat, 2)';
information = sd .* conflict;
w = information / sum(information);

mmlib_report('CRITIC 赋权', sprintf('权重=%s', mat2str(round(w, 4))), ...
    sprintf('标准差=%s', mat2str(round(sd, 4))), sprintf('冲突性=%s', mat2str(round(conflict, 4))));
T = table("X" + string(1:numel(w))', sd', conflict', information', w', ...
    'VariableNames', {'指标', '标准差', '冲突性', '信息量', '权重'});
mmlib_savetable(here, 'critic_weight', T);
