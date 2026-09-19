% 蒙特卡洛积分与收敛性分析（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
nList = [100 1000 10000 100000 1000000];
estimates = zeros(size(nList)); errors = zeros(size(nList));
for i = 1:numel(nList)
    s = exp(rand(nList(i), 1));
    estimates(i) = mean(s);
    errors(i) = std(s) / sqrt(nList(i));
end
trueValue = exp(1) - 1;

mmlib_report('蒙特卡洛积分', sprintf('真值=%.6f', trueValue), ...
    sprintf('最大样本估计=%.6f', estimates(end)), sprintf('标准误=%.2e', errors(end)));
mmlib_savetable(here, 'monte_carlo_integration', table(nList', estimates', errors', ...
    'VariableNames', {'样本量', '估计值', '标准误'}));

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
