% 设定二项分布的参数
n = 100; % 样本量
p = 0.5; % 成功概率

% 计算二项分布的均值和方差
mu = n * p;
sigma = sqrt(n * p * (1 - p));

% 生成x轴的范围，从0到n
x = 0:n;

% 计算二项分布的概率质量函数
bino_pdf = binopdf(x, n, p);

% 生成连续的x轴值用于绘制正态分布曲线
x_cont = linspace(mu - 3*sigma, mu + 3*sigma, 500);

% 计算正态分布的概率密度函数
norm_pdf = normpdf(x_cont, mu, sigma);

% 创建一个新的图形窗口
figure;

% 绘制二项分布的概率质量函数，颜色改为浅蓝色
bar(x, bino_pdf, 'FaceColor', [0.65 0.75 0.85], 'EdgeColor', [0.65 0.75 0.85]);
hold on; % 保持当前图形并允许添加新图形

% 绘制正态分布的概率密度函数，颜色改为稍微深一点的蓝色
plot(x_cont, norm_pdf, 'Color', [0.55 0.5 0.85], 'LineWidth', 2);

% 添加图例
legend('二项分布', '正态分布', 'Location', 'northwest', 'FontSize', 12);

% 设置图形标题和坐标轴标签
title('二项分布与正态分布对比', 'FontSize', 14);
xlabel('成功的数量', 'FontSize', 12);
ylabel('概率质量/密度', 'FontSize', 12);

% 设置坐标轴范围
xlim([0 n]);
ylim([0 max(bino_pdf)*1.2]);

% 添加网格线
grid on;

% 移除边框
box off;

% 设置背景色
set(gcf, 'Color', 'w'); % 白色背景

% 调整图形框的线条宽度
set(gca, 'LineWidth', 1.5); % 边框线条宽度

% 设置刻度标记的字体大小
set(gca, 'TickLabelInterpreter', 'latex', 'FontSize', 10);

% 释放hold状态
hold off;