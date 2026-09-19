clear;
clc;
close all;

% 参数定义
p1_r = 0.111; % 零配件 1 次品率
p1_p = 4;       % 零配件 1 购买单价
p1t_c = 2;      % 零配件 1 检测成本

p2_r = 0.111;  % 零配件 2 次品率
p2_p = 18;         % 零配件 2 购买单价
p2t_c = 3;      % 零配件 2 检测成本

pt_r = 0.111; % 成品 次品率
a_c = 6;          % 装配成本
pt_c = 3;      % 成品检测成本
m_p = 56;          % 市场售价
r_l = 10;            % 调换损失
d_c = 40;       % 拆解费用

% 计算用户退回次品的概率
return_defect_rate = p1_r + p2_r - p1_r * p2_r + pt_r;

% 动态规划表
dp = zeros(2, 2, 2, 2, 2); % [是否检测P1, 是否检测P2, 是否检测成品, 是否拆解, 是否处理退货]

% 初始化动态规划表
dp(:) = -Inf; % 初始利润设置为负无穷

% 动态规划迭代
for p1_test = 0:1
    for p2_test = 0:1
        for prod_test = 0:1
            for disassemble = 0:1
                for handle_return = 0:1
                    % 计算零配件成本
                    p1_cost = p1_p + p1_test * p1t_c;
                    p2_cost = p2_p + p2_test * p2t_c;
                    base_cost = p1_cost + p2_cost + a_c;

                    % 成品基础成本
                    product_cost_base = base_cost;

                    % 成品检测
                    if prod_test
                        product_cost_base = product_cost_base + pt_c;
                        if rand() < pt_r
                            if disassemble
                                product_cost_base = product_cost_base + d_c;
                            else
                                product_cost_base = product_cost_base + r_l;
                            end
                        end
                    end

                    % 返回次品处理
                    if handle_return
                        if rand() < return_defect_rate
                            product_cost_base = product_cost_base + d_c;
                        end
                        product_cost_base = product_cost_base + r_l;
                    end

                    % 计算利润
                    profit = m_p - product_cost_base;

                    % 更新动态规划表
                    dp(p1_test + 1, p2_test + 1, prod_test + 1, disassemble + 1, handle_return + 1) = max(dp(p1_test + 1, p2_test + 1, prod_test + 1, disassemble + 1, handle_return + 1), profit);
                end
            end
        end
    end
end

% 查找最大利润及对应的决策
[max_profit, idx] = max(dp(:));
[best_p1_test, best_p2_test, best_prod_test, best_disassemble, best_handle_return] = ind2sub(size(dp), idx);

% 输出最优解
fprintf('最优解:\n');
fprintf('是否检测零配件1: %d\n', best_p1_test - 1);
fprintf('是否检测零配件2: %d\n', best_p2_test - 1);
fprintf('是否检测成品: %d\n', best_prod_test - 1);
fprintf('是否拆解不合格成品: %d\n', best_disassemble - 1);
fprintf('是否处理退货: %d\n', best_handle_return - 1);
fprintf('平均利润: %.2f\n',max_profit);

% 可视化决策方案的平均利润
figure;

% 创建条形图
bar(reshape(dp, [], 1));
set(gca,'XTick', 1:numel(dp));
set(gca, 'XTickLabel');
xtickangle(45);
xlabel('决策方案');
ylabel('平均利润');
title('各决策方案的平均利润');