function p = mmlib_savetable(here, name, T)
% 把 table 写入 <algorithm>/out/<name>.csv，返回文件路径。
d = mmlib_outdir(here);
p = fullfile(d, [name '.csv']);
writetable(T, p, 'Encoding', 'UTF-8');
fprintf('  结果表 -> %s.csv\n', name);
end
