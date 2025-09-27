function [ICApplied_data] = applyICA(data)

%ICApplied_data = [];

% Loop through each field in the struct
for i = 1:length(data)

    cfg        = [];
    cfg.method = 'fastica'; 

    ICApplied_data(i) = ft_componentanalysis(cfg, data(i));

end

end