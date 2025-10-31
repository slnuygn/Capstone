cfg          = [];
cfg.colorbar = 'yes';
cfg.zlim     = 'maxabs';
cfg.ylim     = [10 Inf];  % plot alpha band upwards
cfg.layout   = 'natmeg_customized_eeg1005.lay';
cfg.channel  = 'EEG126';

figure;
ft_singleplotTFR(cfg, spectr_target);
title('Target condition');

figure;
ft_singleplotTFR(cfg, spectr_standard);
title('Standard condition');

figure;
ft_singleplotTFR(cfg, spectr_novelty);
title('Novelty condition');
