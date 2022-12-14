function [tout, yout] = run_neural(u)
    assignin('base','u',u);
    assignin('base','T',u(length(u)));
    
    result = sim('narmamaglev_v1', ...
        'StopTime', 'T', ...
        'LoadExternalInput', 'on', 'ExternalInput', 'u', ...
        'SaveTime', 'on', 'TimeSaveName', 'tout', ...
        'SaveOutput', 'on', 'OutputSaveName', 'yout', ...
        'SaveFormat', 'Array');
    tout = result.tout;
    yout = result.yout;
end
