% 元胞自动机 · 森林火灾传播（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
n = 60; steps = 60; pGrow = 0.05; pFire = 0.25;
EMPTY = 0; TREE = 1; FIRE = 2;

grid_ = double(rand(n, n) < 0.6);
grid_(round(n/2), round(n/2)) = FIRE;
frames = zeros(n, n, steps + 1); frames(:, :, 1) = grid_;
stats = zeros(steps, 3);

for k = 1:steps
    burning = (grid_ == FIRE);
    infectious = (circshift(burning, 1, 1) | circshift(burning, -1, 1) | ...
                  circshift(burning, 1, 2) | circshift(burning, -1, 2));
    newGrid = grid_;
    catchMask = (grid_ == TREE) & infectious & (rand(n, n) < pFire);
    newGrid(catchMask) = FIRE;
    newGrid(burning) = EMPTY;
    newGrid((grid_ == EMPTY) & (rand(n, n) < pGrow)) = TREE;
    grid_ = newGrid;
    frames(:, :, k + 1) = grid_;
    stats(k, :) = [mean(grid_(:) == TREE), mean(grid_(:) == FIRE), mean(grid_(:) == EMPTY)];
end

mmlib_report('元胞自动机', sprintf('网格=%d', n), sprintf('步数=%d', steps), ...
    sprintf('末步树木比例=%.4f', stats(end, 1)), sprintf('末步着火比例=%.4f', stats(end, 2)));
mmlib_savetable(here, 'cellular_automata', table((1:steps)', stats(:, 1), stats(:, 2), stats(:, 3), ...
    'VariableNames', {'步', '树木比例', '着火比例', '空地比例'}));

% 图件由 Python 生成（技能规则：交付图必须用 Python 绘制，MATLAB 仅负责计算）
