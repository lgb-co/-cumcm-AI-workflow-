% Mann-Kendall 趋势检验（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
x = (0.35 * (0:39)' + randn(40, 1) * 1.2 + 10);
n = numel(x);

s = 0;
for i = 1:n-1
    s = s + sum(sign(x(i+1:end) - x(i)));
end
[~, ~, counts] = unique(x);
tie = sum(counts .* (counts - 1) .* (2 * counts + 5));
varS = (n * (n - 1) * (2 * n + 5) - tie) / 18;
if s > 0
    z = (s - 1) / sqrt(varS);
elseif s < 0
    z = (s + 1) / sqrt(varS);
else
    z = 0;
end
p = 2 * (1 - normcdf(abs(z)));

slopes = [];
for i = 1:n-1
    slopes = [slopes; (x(i+1:end) - x(i)) ./ (1:(n - i))']; %#ok<AGROW>
end
sen = median(slopes);

mmlib_report('Mann-Kendall', sprintf('Z=%.4f', z), sprintf('p值=%.4f', p), ...
    sprintf('Sen斜率=%.4f', sen), sprintf('结论=%s', string(p < 0.05)));
T = table(["Z"; "p"; "Sen斜率"], [z; p; sen], 'VariableNames', {'统计量', '数值'});
mmlib_savetable(here, 'mann_kendall_trend', T);
