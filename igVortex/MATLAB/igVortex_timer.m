clc;

f = @() igVortex();

results = timeit(f);

disp('Results = ');
disp(results);