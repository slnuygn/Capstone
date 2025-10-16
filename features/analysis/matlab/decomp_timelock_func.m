function ERP_data = decomp_timelock_func(data_ICApplied_clean)
% decomposition
% separate trials 'S200' 'S201' 'S202'

numTrials = numel(data_ICApplied_clean);

data_ICApplied_clean_decomp = struct( ...
    'target_data', cell(1, numTrials), ...
    'standard_data', cell(1, numTrials), ...
    'novelty_data', cell(1, numTrials));

for i = 1:numTrials
    [data_ICApplied_clean_decomp(i).target_data, ...
        data_ICApplied_clean_decomp(i).standard_data, ...
        data_ICApplied_clean_decomp(i).novelty_data] = decompose(data_ICApplied_clean(i));
end

% time lock analysis
ERP_data = struct( ...
    'target', cell(1, numTrials), ...
    'standard', cell(1, numTrials), ...
    'novelty', cell(1, numTrials));

for i = 1:numTrials
    cfg = [];
    cfg.latency = [-1 1.5];
    
    ERP_data(i).target = ft_timelockanalysis(cfg, data_ICApplied_clean_decomp(i).target_data);
    ERP_data(i).standard = ft_timelockanalysis(cfg, data_ICApplied_clean_decomp(i).standard_data);
    ERP_data(i).novelty = ft_timelockanalysis(cfg, data_ICApplied_clean_decomp(i).novelty_data);
end

%% separate into classes and extract the ERP data (avg)
% for now commenting out the code without deleting it
% For old group
%old_target = extract_erp_data(ERP_data, 'target');
%old_standard = extract_erp_data(ERP_data, 'standard');
%old_novelty = extract_erp_data(ERP_data, 'novelty');
end
