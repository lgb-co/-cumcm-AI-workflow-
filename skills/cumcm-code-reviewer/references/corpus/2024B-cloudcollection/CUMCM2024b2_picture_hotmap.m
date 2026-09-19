clear;
clc;
close all;

% 参数定义
p1_r = 0.10; % 零配件 1 次品率
p1_p = 4;    % 零配件 1 购买单价
p1t_c = 2;   % 零配件 1 检测成本

p2_r = 0.10; % 零配件 2 次品率
p2_p = 18;   % 零配件 2 购买单价
p2t_c = 3;   % 零配件 2 检测成本

pt_r = 0.20; % 成品 次品率
a_c = 6;     % 装配成本
pt_c = 3;    % 成品检测成本
m_p = 56;    % 市场售价
r_l = 10;     % 调换损失
d_c = 40;     % 拆解费用

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

% 选择提取的维度
% 例如提取 '是否检测零配件1' 维度（p1_test），并将其他维度展平成二维矩阵
p1_test_index = 1; % 提取 '是否检测零配件1' 的情况（1 或 2）

% 提取特定维度的元素
dp_extracted = squeeze(dp(p1_test_index, :, :, :, :));

% 展平成二维矩阵
% 这里我们将 [是否检测零配件2] 和 [是否检测成品] 作为行，其他维度作为列
dp_2d = reshape(dp_extracted, [2*2, 2*2]);

% 创建热力图
figure;
heatmap(dp_2d);
xlabel('是否检测成品 和 是否拆解');
ylabel('是否检测零配件2 和 是否处理退货');
title('各决策组合的利润热力图');

% 添加色标
colorbar;

% 设置热力图颜色
colormap(jet); % 或者其他色彩方案如 'hot', 'parula' 等
