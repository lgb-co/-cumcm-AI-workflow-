% Bass 扩散模型（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
trueP = 0.02; trueQ = 0.35; trueM = 500;
t = (0:19)';
bass = @(p, q, m, tt) m * (1 - exp(-(p + q) * tt)) ./ (1 + (q / p) * exp(-(p + q) * tt));
series = bass(trueP, trueQ, trueM, t);

model = @(prm, tt) bass(prm(1), prm(2), prm(3), tt);
prm0 = [0.01; 0.3; max(series) * 1.2];
prm = lsqcurvefit(model, prm0, t, series, [1e-6; 1e-6; max(series)], [1; 5; max(series) * 50], ...
    optimoptions('lsqcurvefit', 'Display', 'off'));

fitted = model(prm, t);
tFuture = (t(end) + 1:t(end) + 8)';
forecast = model(prm, tFuture);
peakTime = log(prm(2) / prm(1)) / (prm(1) + prm(2));

mmlib_report('Bass 扩散', sprintf('p=%.4f', prm(1)), sprintf('q=%.4f', prm(2)), ...
    sprintf('市场潜力m=%.1f', prm(3)), sprintf('拐点时刻=%.2f', peakTime), ...
    sprintf('预测末期=%.1f', forecast(end)));
T = table([t; tFuture], [fitted; forecast], 'VariableNames', {'时间', '累计采纳'});
mmlib_savetable(here, 'bass_diffusion', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
