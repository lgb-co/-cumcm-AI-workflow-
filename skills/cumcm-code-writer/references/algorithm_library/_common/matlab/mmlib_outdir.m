function d = mmlib_outdir(here)
% 返回模板的输出目录 <algorithm>/out 并确保存在。
d = fullfile(here, '..', 'out');
if ~exist(d, 'dir')
    mkdir(d);
end
end
