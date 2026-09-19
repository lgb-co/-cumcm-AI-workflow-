function matlab_smoke()
% MATLAB 模板批量烟测：在一个 MATLAB 会话内依次运行全部 templates 的 main.m。
% 用法：在当前目录执行  matlab -batch "matlab_smoke"
% 每个模板在独立函数作用域中运行，避免脚本变量互相污染。
here = fileparts(mfilename('fullpath'));            % ...\代码编写\scripts
root = fullfile(fileparts(here), 'references', 'algorithm_library');
categories = dir(root);
passCount = 0; failCount = 0; failures = {};
for i = 1:numel(categories)
    category = categories(i).name;
    if ~categories(i).isdir || strcmp(category, '.') || strcmp(category, '..') || strcmp(category, '_common')
        continue
    end
    algorithms = dir(fullfile(root, category));
    for j = 1:numel(algorithms)
        algo = algorithms(j).name;
        if ~algorithms(j).isdir || strcmp(algo, '.') || strcmp(algo, '..')
            continue
        end
        workDir = fullfile(root, category, algo, 'matlab');
        if ~exist(fullfile(workDir, 'main.m'), 'file')
            continue
        end
        [ok, message] = run_one(workDir);
        if ok
            fprintf('PASS %s/%s\n', category, algo);
            passCount = passCount + 1;
        else
            fprintf('FAIL %s/%s :: %s\n', category, algo, strrep(message, '%', '%%'));
            failCount = failCount + 1;
            failures{end + 1} = sprintf('%s/%s: %s', category, algo, message); %#ok<AGROW>
        end
    end
end
fprintf('SUMMARY pass=%d fail=%d\n', passCount, failCount);
if ~isempty(failures)
    fprintf('---- failure list ----\n');
    for k = 1:numel(failures)
        fprintf('%s\n', strrep(failures{k}, '%', '%%'));
    end
end
end

function [ok, message] = run_one(workDir)
ok = true; message = '';
try
    cd(workDir);
    run('main.m');
catch err
    ok = false;
    message = err.message;
end
close all;
end