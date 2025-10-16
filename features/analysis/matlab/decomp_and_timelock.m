%% decomposition

% separate trials 'S200' 'S201' 'S202'


for i = 1:length(old_clean)
    
    [old_clean_decomp(i).target_old, old_clean_decomp(i).standard_old, old_clean_decomp(i).novelty_old] = decompose(old_clean(i));
    
end




%% time lock analysis


for i = 1: length(old_clean_decomp)
    
    cfg = [];
    cfg.latency = [0 1];
    
    ERP_old(i).target = ft_timelockanalysis(cfg, old_clean_decomp(i).target_old);
    
    ERP_old(i).standard = ft_timelockanalysis(cfg, old_clean_decomp(i).standard_old);
    
    ERP_old(i).novelty = ft_timelockanalysis(cfg, old_clean_decomp(i).novelty_old);
    
end


%% separate into classes and extract the ERP data (avg)

% For old group
old_target = extract_erp_data(ERP_old, 'target');
old_standard = extract_erp_data(ERP_old, 'standard');
old_novelty = extract_erp_data(ERP_old, 'novelty');







