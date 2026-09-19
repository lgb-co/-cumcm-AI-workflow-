% 因子分析（MATLAB 最小可运行模板，依赖 Statistics and Machine Learning Toolbox）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
f1 = randn(300, 1); f2 = randn(300, 1);
X = [0.9*f1 + 0.4*randn(300,1), 0.8*f1 + 0.4*randn(300,1), 0.85*f2 + 0.4*randn(300,1), ...
     0.7*f2 + 0.4*randn(300,1), randn(300,1)];

nFactors = 2;
[loadings, ~] = factoran(X, nFactors, 'rotate', 'varimax');
communality = sum(loadings.^2, 2);

C = corr(X);
invC = inv(C);
partial = -invC ./ sqrt(diag(invC) * diag(invC)');
partial(logical(eye(size(C)))) = 0;
offDiag = C - eye(size(C));
kmo = sum(sum(offDiag.^2)) / (sum(sum(offDiag.^2)) + sum(sum(partial.^2)));

mmlib_report('因子分析', sprintf('因子数=%d', nFactors), sprintf('KMO=%.4f', kmo), ...
    sprintf('共同度=%s', mat2str(round(communality', 4))));
T = array2table(round(loadings, 6), 'VariableNames', "因子" + string(1:nFactors));
T = addvars(T, communality, 'Before', 1, 'NewVariableNames', '共同度');
mmlib_savetable(here, 'factor_analysis', T);
