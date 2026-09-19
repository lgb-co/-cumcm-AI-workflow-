% 缺失值插补（MATLAB 最小可运行模板）
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', '_common', 'matlab'));

rng(42);
years = (2000:2019)';
gdp = 1000 + 45 * (0:19)' + 20 * randn(20, 1);
pop = 800 + 6 * (0:19)' + 5 * randn(20, 1);
gdp([4 10 16]) = NaN; pop([6 13]) = NaN;

gdpFilled = fillmissing(gdp, 'linear', 'EndValues', 'nearest');
popFilled = fillmissing(pop, 'linear', 'EndValues', 'nearest');

mmlib_report('缺失值插补', sprintf('GDP缺失=%d', sum(isnan(gdp))), ...
    sprintf('人口缺失=%d', sum(isnan(pop))), ...
    sprintf('原始GDP均值=%.4f', mean(gdp, 'omitnan')), ...
    sprintf('插补后均值=%.4f', mean(gdpFilled)));
T = table(years, gdp, gdpFilled, pop, popFilled, ...
    'VariableNames', {'年份', 'GDP原始', 'GDP插补', '人口原始', '人口插补'});
mmlib_savetable(here, 'missing_imputation', T);
