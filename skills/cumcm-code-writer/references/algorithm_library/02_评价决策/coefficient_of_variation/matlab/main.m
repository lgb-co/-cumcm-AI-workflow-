% 变异系数法 · 客观赋权（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

X = [92 0.83 3.1 8; 78 0.71 4.5 6; 85 0.90 2.7 9; 70 0.64 5.2 5; 88 0.79 3.6 7];

cv = std(X, 0, 1) ./ mean(X, 1);
w = cv / sum(cv);

mmlib_report('变异系数法', sprintf('权重=%s', mat2str(round(w, 4))), sprintf('变异系数=%s', mat2str(round(cv, 4))));
T = table("X" + string(1:numel(w))', cv', w', 'VariableNames', {'指标', '变异系数', '权重'});
mmlib_savetable(here, 'coefficient_of_variation', T);
