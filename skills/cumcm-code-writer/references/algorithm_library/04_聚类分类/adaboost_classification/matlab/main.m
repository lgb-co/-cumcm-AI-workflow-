% AdaBoost 集成分类（MATLAB 最小可运行模板，依赖 Statistics and Machine Learning Toolbox）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
X = randn(400, 5);
score = 1.4*X(:, 1) - 1.1*X(:, 2) + 0.9*X(:, 3).*X(:, 4) + 0.6*randn(400, 1);
y = double(score > 0);

cv = cvpartition(y, 'HoldOut', 0.3);
model = fitcensemble(X(training(cv), :), y(training(cv)), 'Method', 'AdaBoostM1', ...
    'NumLearningCycles', 200, 'LearnRate', 0.5);
pred = predict(model, X(test(cv), :));
accuracy = mean(pred == y(test(cv)));
trainAcc = 1 - resubLoss(model);

mmlib_report('AdaBoost', sprintf('测试准确率=%.4f', accuracy), ...
    sprintf('弱学习器数=%d', numel(model.Trained)), sprintf('训练集准确率=%.4f', trainAcc));
T = table((1:numel(model.Trained))', 1 - resubLoss(model, 'Mode', 'cumulative'), ...
    'VariableNames', {'轮次', '训练准确率'});
mmlib_savetable(here, 'adaboost_classification', T);

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
