% MCMC · Metropolis-Hastings 抽样（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
nSamples = 20000; proposalSd = 1.2; burnIn = 2000;
logTarget = @(x) -0.5 * x.^2;
samples = zeros(nSamples, 1);
current = 0; logCurrent = logTarget(0); accepted = 0;
for i = 1:nSamples
    proposal = current + proposalSd * randn();
    logProposal = logTarget(proposal);
    if log(rand) < logProposal - logCurrent
        current = proposal; logCurrent = logProposal; accepted = accepted + 1;
    end
    samples(i) = current;
end
kept = samples(burnIn+1:end);

mmlib_report('MCMC', sprintf('接受率=%.4f', accepted/nSamples), ...
    sprintf('后验均值=%.4f', mean(kept)), sprintf('后验标准差=%.4f', std(kept)), ...
    sprintf('有效样本=%d', numel(kept)));
mmlib_savetable(here, 'mcmc_metropolis', table((1:500)', kept(1:500), 'VariableNames', {'样本', '取值'}));

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
