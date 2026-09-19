% Bootstrap 重采样（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
data = lognrnd(1.0, 0.6, 60, 1);
nBoot = 5000; n = numel(data);
means = zeros(nBoot, 1); medians = zeros(nBoot, 1);
for b = 1:nBoot
    idx = randi(n, n, 1);
    resample = data(idx);
    means(b) = mean(resample); medians(b) = median(resample);
end
ci = @(v) quantile(v, [0.025 0.975]);

mmlib_report('Bootstrap', sprintf('样本量=%d', n), sprintf('重采样次数=%d', nBoot), ...
    sprintf('均值区间=%s', mat2str(round(ci(means), 4))), ...
    sprintf('中位数区间=%s', mat2str(round(ci(medians), 4))));
T = table((1:500)', means(1:500), medians(1:500), 'VariableNames', {'重采样序号', '均值', '中位数'});
mmlib_savetable(here, 'bootstrap_resampling', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
