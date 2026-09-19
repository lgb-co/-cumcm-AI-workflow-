% 灰色预测 GM(1,1)（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

x0 = [2.7 3.1 3.6 4.2 4.9 5.7 6.6]';
steps = 3; n = numel(x0);

ratio = x0(1:end-1) ./ x0(2:end);
low = exp(-2/(n + 1)); high = exp(2/(n + 1));
ratioOK = all(ratio > low & ratio < high);

x1 = cumsum(x0);
z1 = 0.5 * (x1(2:end) + x1(1:end-1));
B = [-z1 ones(n - 1, 1)];
Y = x0(2:end);
params = B \ Y; a = params(1); b = params(2);

k = 0:(n - 1);
x1hat = (x0(1) - b/a) * exp(-a*k) + b/a;
fitted = [x0(1); diff(x1hat)'];
kFuture = n:(n + steps - 1);
x1future = (x0(1) - b/a) * exp(-a*kFuture) + b/a;
x1prev = (x0(1) - b/a) * exp(-a*(kFuture - 1)) + b/a;
forecast = (x1future - x1prev)';

C = std(x0 - fitted, 0) / std(x0, 0);
mmlib_report('GM(1,1)', sprintf('a=%.4f', a), sprintf('b=%.4f', b), sprintf('后验差比C=%.4f', C), ...
    sprintf('级比检验=%s', string(ratioOK)), sprintf('预测值=%s', mat2str(round(forecast', 4))));
T = table((1:(n + steps))', [fitted; forecast], 'VariableNames', {'序号', '数值'});
mmlib_savetable(here, 'gm11', T);
