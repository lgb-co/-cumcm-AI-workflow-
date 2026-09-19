clear;
clc;
close all;

% 参数定义
% 零部件参数
pd_r = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]; % 各零部件次品率
p_p = [2, 8, 12, 2, 8, 12, 2, 8]; % 各零部件购买单价
pt_c = [1, 1, 2, 1, 1, 2, 1, 2]; % 各零部件检测成本

% 半成品参数
sd_r = [0.1, 0.1, 0.1]; % 各半成品次品率
st_c = [4, 4, 4]; % 各半成品检测成本
sa_c = [3, 3, 3]; % 各半成品组装成本
schai_c = [5, 5, 5]; % 各半成品拆解成本

% 成品参数
p0d_r = 0.1; % 成品次品率
a_c = 8; % 装配成本
p0t_c = 6; % 成品检测成本
price = 200; % 市场售价
r_l = 40; % 调换损失
p0chai_c = 10; % 成品拆解成本

% 动态规划表
num_p = length(pd_r);
num_s = length(sd_r);

dp = zeros(2^num_p, 2^num_s, 2, 2, 2, 2); % [零部件检测组合, 半成品检测组合, 是否检测成品, 是否拆解半成品, 是否拆解成品, 是否处理退货]

% 初始化动态规划表
dp(:) = inf; % 初始利润设置为无穷大

% 动态规划迭代
for p0_t = 0:1
    for chai_s = 0:1
        for chai_p = 0:1
            for tuihui = 0:1
                % 遍历所有零部件检测组合
                for p_t = 0:(2^num_p - 1)
                    % 遍历所有半成品检测组合
                    for sp_t = 0:(2^num_s - 1)
                        % 计算零配件成本
                        p_c = 0;
                        pt_c0 = 0;
                        for i = 1:num_p
                            if bitget(p_t, num_p - i + 1)
                                p_c = p_c + p_p(i) + pt_c(i);
                                pt_c0 = pt_c0 + pt_c(i);
                            else
                                p_c = p_c + p_p(i);
                            end
                        end
                        
                        % 计算半成品成本
                        s_c = 0;
                        st_c0 = 0;
                        sa_c0 = 0;
                        schai_c0 = 0;
                        for i = 1:num_s
                            if bitget(sp_t, num_s - i + 1)
                                s_c = s_c + st_c(i);
                                st_c0 = st_c0 + st_c(i);
                                if rand() < sd_r(i)
                                    if chai_s
                                        schai_c0 = schai_c0 + schai_c(i);
                                    end
                                end
                            end
                            sa_c0 = sa_c0 + sa_c(i);
                        end
                        
                        
                        % 成品基础成本
                        p0_cb = p_c + s_c + sa_c0 + a_c;
                        
                        % 成品检测
                        if p0_t
                            p0_cb = p0_cb + p0t_c;
                            if rand() < p0d_r
                                if chai_p
                                    p0_cb = p0_cb + p0chai_c;
                                    % 拆解成品后可以回收零部件
                                    for i = 1:num_p
                                        p0_cb = p0_cb - p_p(i);
                                    end
                                else
                                    p0_cb = p0_cb + r_l;
                                end
                            end
                        end
                        
                        % 返回次品处理
                        if tuihui
                            if rand() < p0d_r
                                p0_cb = p0_cb + p0chai_c;
                                % 拆解成品后可以回收零部件
                                for i = 1:num_p
                                    p0_cb = p0_cb - p_p(i);
                                end
                            end
                            p0_cb = p0_cb + r_l;
                        end
                        
                        % 更新动态规划表
                        dp(p_t + 1, sp_t + 1, p0_t + 1, chai_s + 1, chai_p + 1, tuihui + 1) = min(dp(p_t + 1, sp_t + 1, p0_t + 1, chai_s + 1, chai_p + 1, tuihui + 1), p0_cb + schai_c0);
                    end
                end
            end
        end
    end
end

% 查找最小成本及对应的决策
[min_cost, idx] = min(dp(:));
[bp_t, bs_t, bp0_t, bchai_s, bchai_p0, btuihui] = ind2sub(size(dp), idx);

% 解码最佳零部件检测组合
bp_ts = dec2bin(bp_t - 1, num_p) - '0';

% 解码最佳半成品检测组合
bs_ts = dec2bin(bs_t - 1, num_s) - '0';

% 输出最优解
fprintf('最优解:\n');
fprintf('零部件检测:\n');
for i = 1:num_p
    fprintf('零部件%d: %d\n', i, bp_ts(num_p - i + 1));
end
fprintf('半成品检测:\n');
for i = 1:num_s
    fprintf('半成品%d: %d\n', i, bs_ts(num_s - i + 1));
end
fprintf('是否检测成品: %d\n', bp0_t - 1);
fprintf('是否拆解不合格半成品: %d\n', bchai_s - 1);
fprintf('是否拆解不合格成品: %d\n', bchai_p0 - 1);
fprintf('是否处理退货: %d\n', btuihui - 1);
fprintf('平均利润: %.2f\n', min_cost);


