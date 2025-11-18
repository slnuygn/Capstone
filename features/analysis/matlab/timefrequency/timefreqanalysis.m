cfg         = [];

% not sure of these, ask the teacher
cfg.output     = 'pow';
cfg.channel    = 'all';
cfg.method     = 'mtmconvol';
cfg.taper      = 'hanning';
cfg.toi        = -1 : 0.10 : 1.5;
cfg.foi        = 2:2:40;
cfg.t_ftimwin  = ones(size(cfg.foi)) * 0.5;

cfg.trials   = find(data.trialinfo(:,1) == S200);
freq_target = ft_freqanalysis(cfg, data);

cfg.trials   = find(data.trialinfo(:,1) == S201);
freq_standard = ft_freqanalysis(cfg, data);

cfg.trials   = find(data.trialinfo(:,1) == S202);
freq_novelty = ft_freqanalysis(cfg, data);