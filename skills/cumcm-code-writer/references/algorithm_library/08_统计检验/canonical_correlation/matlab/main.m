% 典型相关分析 CCA（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
latent = randn(150, 1);
X = latent * [0.9 0.4 0.2] + 0.5 * randn(150, 3);
Y = latent * [0.8 0.5] + 0.5 * randn(150, 2);

[A, B, r, U, V] = canoncorr(X, Y);

mmlib_report('典型相关分析', sprintf('典型相关系数=%s', mat2str(round(r, 4))), ...
    sprintf('X载荷=%s', mat2str(round(A(:, 1), 4))), sprintf('Y载荷=%s', mat2str(round(B(:, 1), 4))));
T = table((1:numel(r))', r', 'VariableNames', {'序号', '典型相关系数'});
mmlib_savetable(here, 'canonical_correlation', T);
