clear;
clc;
close all;

% 参数定义
p1_r = 0.10; % 零配件1次品率
p1_p = 4;          % 零配件1购买单价
p1t_c = 2;      % 零配件1检测成本

p2_r = 0.10;  % 零配件2次品率
p2_p = 18;         % 零配件2购买单价
p2t_c = 3;      % 零配件 2 检测成本

pt_r = 0.20; % 成品次品率
a_c = 6;          % 装配成本
pt_c = 3;      % 成品检测成本
m_p = 56;          % 市场售价
r_l = 6;            % 调换损失
d_c = 5;       % 拆解费用

% 计算用户退回次品的概率
return_r = p1_r + p2_r - p1_r * p2_r + pt_r;

% 动态规划表
dp = zeros(2, 2, 2, 2, 2); % [是否检测P1, 是否检测P2, 是否检测成品, 是否拆解, 是否处理退货]

dp(:) = -Inf; % 初始利润设置为负无穷

% 动态规划迭代
for p1_t = 0:1
    for p2_t = 0:1
        for prod_t = 0:1
            for chaijie = 0:1
                for tuihui = 0:1
                    % 计算零配件成本
                    p1_c = p1_p + p1_t * p1t_c;
                    p2_c = p2_p + p2_t * p2t_c;
                    c1 = p1_c + p2_c + a_c;

                    % 成品基础成本
                    c2 = c1;

                    % 成品检测
                    if prod_t
                        c2 = c2 + pt_c;
                        if rand() < pt_r
                            if chaijie
                                c2 = c2 + d_c;
                            else
                                c2 = c2 + r_l;
                            end
                        end
                    end

                    % 返回次品处理
                    if tuihui
                        if rand() < return_r
                            c2 = c2 + d_c;
                        end
                        c2 = c2 + r_l;
                    end

                    % 计算利润
                    profit = m_p - c2;

                    % 更新动态规划表
                    dp(p1_t + 1, p2_t + 1, prod_t + 1, chaijie + 1, tuihui + 1) = max(dp(p1_t + 1, p2_t + 1, prod_t + 1, chaijie + 1, tuihui + 1), profit);
                end
            end
        end
    end
end

% 查找最大利润及对应的决策
[max_profit, idx] = max(dp(:));
a = mean(dp(:))
[bp1_t, bp2_t, bprod_t, bchajie, btuihui] = ind2sub(size(dp), idx);

% 输出最优解
fprintf('最优解:\n');
fprintf('是否检测零配件1: %d\n', bp1_t - 1);
fprintf('是否检测零配件2: %d\n', bp2_t - 1);
fprintf('是否检测成品: %d\n', bprod_t - 1);
fprintf('是否拆解不合格成品: %d\n', bchajie - 1);
fprintf('是否处理退货: %d\n', btuihui - 1);
fprintf('最大利润: %.2f\n', max_profit);

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