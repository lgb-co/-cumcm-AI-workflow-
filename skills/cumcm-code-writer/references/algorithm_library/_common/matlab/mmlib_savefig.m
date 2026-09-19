function mmlib_savefig(here, fig, name)
% 同时保存 300dpi PNG 与矢量 PDF 到 <algorithm>/out。
d = mmlib_outdir(here);
exportgraphics(fig, fullfile(d, [name '.png']), 'Resolution', 300);
exportgraphics(fig, fullfile(d, [name '.pdf']), 'ContentType', 'vector');
fprintf('  图 -> %s.png / %s.pdf\n', name, name);
end
