function mmlib_report(title, varargin)
% 统一报告输出：[标题] key=value 形式，便于与 Python 模板对照。
if isempty(varargin)
    fprintf('[%s]\n', title);
    return
end
parts = cell(1, numel(varargin));
for k = 1:numel(varargin)
    if ischar(varargin{k})
        parts{k} = varargin{k};
    else
        parts{k} = num2str(varargin{k});
    end
end
fprintf('[%s] %s\n', title, strjoin(parts, '  '));
end
