% 单因素方差分析（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
groups = [randn(30, 1) + 5.0, randn(30, 1) + 5.6, randn(30, 1) + 6.8];

[p, tbl, statsOut] = anova1(groups, {'方案A', '方案B', '方案C'}, 'off');
F = tbl{2, 5};
leveneP = vartestn(groups, 'TestType', 'LeveneAbsolute', 'Display', 'off');
multi = multcompare(statsOut, 'Display', 'off');

mmlib_report('单因素方差分析', sprintf('F=%.4f', F), sprintf('p值=%.3e', p), ...
    sprintf('方差齐性p=%.4f', leveneP), sprintf('结论=%s', string(p < 0.05)));
T = table(["方案A"; "方案B"; "方案C"], mean(groups)', std(groups)', ...
    'VariableNames', {'组别', '均值', '标准差'});
mmlib_savetable(here, 'anova_oneway', T);
mmlib_savetable(here, 'anova_posthoc', table(multi(:, 1), multi(:, 2), multi(:, 4), ...
    'VariableNames', {'组i', '组j', 'p值'}));
