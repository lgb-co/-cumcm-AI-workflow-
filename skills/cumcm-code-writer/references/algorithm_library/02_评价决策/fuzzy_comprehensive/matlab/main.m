% 模糊综合评价（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

W = [0.30 0.25 0.25 0.20];
R = [0.40 0.35 0.20 0.05; 0.30 0.40 0.20 0.10; 0.20 0.30 0.35 0.15; 0.25 0.35 0.30 0.10];
levels = ["优", "良", "中", "差"];

B = sum(W' .* R, 1);
B = B / sum(B);
[~, k] = max(B);

mmlib_report('模糊综合评价', sprintf('评价向量=%s', mat2str(round(B, 4))), sprintf('等级=%s', levels(k)));
T = table(levels', B', 'VariableNames', {'等级', '隶属度'});
mmlib_savetable(here, 'fuzzy_comprehensive', T);
