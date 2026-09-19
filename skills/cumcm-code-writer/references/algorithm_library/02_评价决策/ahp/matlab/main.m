% 层次分析法 AHP · 指标权重（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

A = [1 2 5; 1/2 1 3; 1/5 1/3 1];
RI = [0 0 0.58 0.90 1.12 1.24 1.32 1.41 1.45];
n = size(A, 1);

[V, D] = eig(A);
[lambdaMax, k] = max(real(diag(D)));
w = abs(V(:, k)); w = w / sum(w);
CI = (lambdaMax - n) / (n - 1);
CR = CI / RI(n);

mmlib_report('层次分析法', sprintf('权重=%s', mat2str(round(w', 4))), sprintf('CR=%.4f', CR), ...
    sprintf('一致性通过=%s', string(CR < 0.1)));
T = table("C" + string(1:n)', w, 'VariableNames', {'指标', '权重'});
mmlib_savetable(here, 'ahp', T);
