% BP 神经网络分类（MATLAB 最小可运行模板）
% 说明：本机无 Deep Learning Toolbox，用单隐藏层 ELM（随机隐层 + 最小二乘输出）实现同样的分类结构。
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
X = [randn(110, 3) * 0.9; randn(110, 3) * 0.9 + [3 2 0]; randn(110, 3) * 0.9 + [1 4 2]];
y = [ones(110, 1); 2 * ones(110, 1); 3 * ones(110, 1)];

idx = randperm(330); trainIdx = idx(1:231); testIdx = idx(232:end);
Xtrain = X(trainIdx, :); Xtest = X(testIdx, :);
labels = unique(y(trainIdx));
T = zeros(numel(labels), numel(trainIdx));
for k = 1:numel(trainIdx)
    T(y(trainIdx(k)), k) = 1;
end

hidden = 24;
W = randn(3, hidden); b = randn(1, hidden);
H = 2 ./ (1 + exp(-2 * (Xtrain * W + b))) - 1;
beta = pinv(H) * T';
scores = (2 ./ (1 + exp(-2 * (Xtest * W + b))) - 1) * beta;
[~, pred] = max(scores, [], 2);
predLabel = labels(pred);
accuracy = mean(predLabel == y(testIdx));
cm = confusionmat(y(testIdx), predLabel);

mmlib_report('MLP 分类', sprintf('测试准确率=%.4f', accuracy), sprintf('类别数=%d', size(cm, 1)));
Tout = table((1:size(cm, 1))', diag(cm) ./ max(1, sum(cm, 2)), 'VariableNames', {'类别', '召回率'});
mmlib_savetable(here, 'mlp_classification', Tout);
