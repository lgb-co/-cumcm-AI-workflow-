% Moran's I 空间自相关分析（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
side = 8; n = side * side;
base = randn(side, side);
smooth = (base + circshift(base, 1, 1) + circshift(base, -1, 1) + ...
          circshift(base, 1, 2) + circshift(base, -1, 2)) / 5;
x = smooth(:);

W = zeros(n, n);
for r = 1:side
    for c = 1:side
        idx = (r - 1) * side + c;
        if c < side, other = (r - 1) * side + c + 1; W(idx, other) = 1; W(other, idx) = 1; end
        if r < side, other = r * side + c; W(idx, other) = 1; W(other, idx) = 1; end
    end
end
W = W ./ sum(W, 2);

z = x - mean(x);
S0 = sum(W(:));
I = n / S0 * (z' * W * z) / (z' * z);
EI = -1 / (n - 1);
VI = (n^2 * sum(W(:).^2) - n * S0) / ((n^2 - 1) * S0^2) - EI^2;
zs = (I - EI) / sqrt(VI);
p = 2 * (1 - normcdf(abs(zs)));

mmlib_report('Moran''s I', sprintf('I=%.4f', I), sprintf('E(I)=%.4f', EI), ...
    sprintf('z=%.4f', zs), sprintf('p=%.4f', p));
T = table(["I"; "E(I)"; "z"; "p"], [I; EI; zs; p], 'VariableNames', {'指标', '数值'});
mmlib_savetable(here, 'moran_i', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
