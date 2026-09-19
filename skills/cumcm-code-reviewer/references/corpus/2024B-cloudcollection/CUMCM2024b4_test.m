clear;
clc;
close all;

% 参数定义
% 零配件参数
p_r = [0.111, 0.111, 0.111, 0.111, 0.111, 0.111, 0.111, 0.111]; % 各零配件次品率
p_p = [2, 8, 12, 2, 8, 12, 2, 8]; % 各零配件购买单价
pt_c = [1, 1, 2, 1, 1, 2, 1, 2]; % 各零配件检测成本

% 半成品参数
prt_r = [0.111, 0.111, 0.111]; % 各半成品次品率
prt_c = [4, 4, 4]; % 各半成品检测成本
pr_c = [3, 3, 3]; % 各半成品成本

% 成品参数
p0_r = 0.111; % 成品次品率
a_c = 8; % 装配成本
p0t_c = 6; % 成品检测成本
price = 200; % 市场售价
r_l = 40; % 调换损失
p0chai_c = 10; % 成品拆解成本

% 自动确定m和n
m = length(p_r); % 零配件数量
n = length(prt_r); % 工序数量

% 动态规划表
dp = -inf(2^m, 2^n, 2, 2, 2, 2); % [零配件检测组合, 工序检测组合, 是否检测成品, 是否拆解不合格半成品, 是否拆解不合格成品, 是否处理退货]

% 初始化动态规划表
dp(:) = -inf; % 初始利润设置为负无穷

% 动态规划迭代
for p_t = 0:1
for chai_s = 0:1
for chai_p0 = 0:1
for tuihui = 0:1
% 遍历所有零配件检测组合
for pa_t = 0:(2^m - 1)
% 遍历所有工序检测组合
for pr_t = 0:(2^n - 1)
% 计算零配件成本
p_cs = 0;
pt_cs = 0;
for i = 1:m
if bitget(pa_t, m - i + 1)
p_cs = p_cs + p_p(i) + pt_c(i);
pt_cs = pt_cs + pt_c(i);
else
p_cs = p_cs + p_p(i);
end
end
% 计算工序成本
pr_cs = 0;
prt_cs = 0;
for i = 1:n
if bitget(pr_t, n - i + 1)
pr_cs = pr_cs + pr_c(i);
prt_cs = prt_cs + prt_c(i);
if rand() < prt_r(i)
if chai_s
pr_cs = pr_cs + 5; % 假设拆解成本为5
end
end
end
end
% 成品基础成本
p0_cb = p_cs + pr_cs + a_c;
% 成品检测
if p_t
p0_cb = p0_cb + p0t_c;
if rand() < p0_r
if chai_p0
p0_cb = p0_cb + p0chai_c;
% 拆解成品后可以回收零部件
for i = 1:m
p0_cb = p0_cb - p_p(i);
end
else
p0_cb = p0_cb + r_l;
end
end
end
% 返回次品处理
if tuihui
if rand() < p0_r
p0_cb = p0_cb + p0chai_c;
% 拆解成品后可以回收零部件
for i = 1:m
p0_cb = p0_cb - p_p(i);
end
end
p0_cb = p0_cb + r_l;
end
% 计算利润
profit = price - p0_cb;
% 更新动态规划表
dp(pa_t + 1, pr_t + 1, p_t + 1, chai_s + 1, chai_p0 + 1, tuihui + 1) = ...
max(dp(pa_t + 1, pr_t + 1, p_t + 1, chai_s + 1, chai_p0 + 1, tuihui + 1), profit);
end
end
end
end
end
end

% 查找最大利润及对应的决策
[max_profit, idx] = max(dp(:));
[bp_t, bpr_t, bp0_t, bchai_s, bchai_p0, btui] = ind2sub(size(dp), idx);

% 解码最佳零配件检测组合
best_part_tests = dec2bin(bp_t - 1, m) - '0';

% 解码最佳工序检测组合
best_proc_tests = dec2bin(bpr_t - 1, n) - '0';

% 输出最优解
fprintf('最优解是:\n');
fprintf('零配件检测:\n');
for i = 1:m
fprintf('零配件%d: %d\n', i, best_part_tests(m - i + 1));
end
fprintf('工序检测:\n');
for i = 1:n
fprintf('工序%d: %d\n', i, best_proc_tests(n - i + 1));
end
fprintf('是否检测成品: %d\n', bp0_t - 1);
fprintf('是否拆解不合格半成品: %d\n', bchai_s - 1);
fprintf('是否拆解不合格成品: %d\n', bchai_p0 - 1);
fprintf('是否处理退货: %d\n', btui - 1);
fprintf('平均最小成本: %.2f\n', max_profit);