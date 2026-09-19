% 贝叶斯参数估计 · Beta-二项共轭模型（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

k = 57; n = 100; alpha0 = 2; beta0 = 2;
alphaPost = alpha0 + k; betaPost = beta0 + n - k;

postMean = alphaPost / (alphaPost + betaPost);
postStd = sqrt(alphaPost * betaPost / ((alphaPost + betaPost)^2 * (alphaPost + betaPost + 1)));
lower = betainv(0.025, alphaPost, betaPost);
upper = betainv(0.975, alphaPost, betaPost);

mmlib_report('贝叶斯估计', sprintf('后验参数=Beta(%.0f, %.0f)', alphaPost, betaPost), ...
    sprintf('后验均值=%.4f', postMean), sprintf('可信区间=[%.4f, %.4f]', lower, upper), ...
    sprintf('频率估计=%.4f', k / n));
T = table(["后验均值"; "后验标准差"; "区间下界"; "区间上界"; "频率估计"], ...
    [postMean; postStd; lower; upper; k / n], 'VariableNames', {'指标', '数值'});
mmlib_savetable(here, 'bayesian_inference', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
