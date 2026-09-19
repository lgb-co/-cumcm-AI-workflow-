function D = mmlib_demo_tsp()
% 10 城市演示实例（与 Python 模板 demo 保持同一坐标），返回对称距离矩阵。
coords = [0 0; 10 0; 20 5; 22 18; 12 26; 0 22; -8 14; -6 4; 8 12; 16 10];
D = squareform(pdist(coords));
end
