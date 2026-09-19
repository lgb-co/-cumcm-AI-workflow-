% 卡方检验（MATLAB 最小可运行模板）
% 独立性检验统计量 chi2 = Σ (O - E)^2 / E，自由度 (r-1)(c-1)；p 值由卡方分布给出。
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

observed = [42 30 18; 28 45 37];
rowSum = sum(observed, 2); colSum = sum(observed, 1); total = sum(observed(:));
expected = rowSum * colSum / total;
chi2 = sum(sum((observed - expected).^2 ./ expected));
dof = (size(observed, 1) - 1) * (size(observed, 2) - 1);
p = 1 - chi2cdf(chi2, dof);
ratio = mean(expected(:) < 5);

mmlib_report('卡方检验', sprintf('卡方值=%.4f', chi2), sprintf('p值=%.4f', p), ...
    sprintf('自由度=%d', dof), sprintf('期望频数不足5的比例=%.0f%%', ratio * 100), ...
    sprintf('结论=%s', string(p < 0.05)));
T = table(expected(:), 'VariableNames', {'期望频数'});
mmlib_savetable(here, 'chi_square_test', T);