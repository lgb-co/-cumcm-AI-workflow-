% Logistic 人口增长模型（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

t = (0:30)';
Ktrue = 120; rtrue = 0.45;
N = Ktrue ./ (1 + (Ktrue/8 - 1) * exp(-rtrue * t));

model = @(p, tt) p(2) ./ (1 + (p(2)/N(1) - 1) * exp(-p(1) * tt));
p0 = [0.3; max(N)];
p = lsqcurvefit(model, p0, t, N, [], [], optimoptions('lsqcurvefit', 'Display', 'off'));

fitted = model(p, t);
tPred = (31:40)';
forecast = model(p, tPred);
rmse = sqrt(mean((fitted - N).^2));

mmlib_report('Logistic 模型', sprintf('增长率r=%.4f', p(1)), sprintf('环境容量K=%.3f', p(2)), ...
    sprintf('拟合RMSE=%.4f', rmse), sprintf('预测末期=%.3f', forecast(end)));
T = table([t; tPred], [fitted; forecast], 'VariableNames', {'时间', '数值'});
mmlib_savetable(here, 'logistic_population', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
