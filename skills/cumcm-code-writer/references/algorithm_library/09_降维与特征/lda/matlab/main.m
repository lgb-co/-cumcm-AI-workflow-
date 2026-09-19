% 线性判别分析 LDA（MATLAB 最小可运行模板，依赖 Statistics and Machine Learning Toolbox）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
X = [randn(90, 3); randn(90, 3) + [2.2 1.6 0.8]];
y = [zeros(90, 1); ones(90, 1)];

mdl = fitcdiscr(X, y);
accuracy = 1 - kfoldLoss(crossval(mdl, 'KFold', 5));
coefficients = mdl.Coeffs(1, 2).Linear;
projection = (X - mean(X)) * coefficients;

mmlib_report('线性判别分析', sprintf('交叉验证准确率=%.4f', accuracy), ...
    sprintf('判别系数=%s', mat2str(round(coefficients', 4))));
T = table(["X1"; "X2"; "X3"], coefficients, 'VariableNames', {'变量', '系数'});
mmlib_savetable(here, 'lda', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
