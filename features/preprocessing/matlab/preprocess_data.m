function [prepped_data] = preprocess_data(data, selected_channels)

cfg= [];
cfg.dataset = data;
cfg.headerfile = ft_read_header(cfg.dataset);
event = ft_read_event(cfg.dataset, 'header', cfg.headerfile);

cfg.trialfun             = 'ft_trialfun_general';     % it will call your function and pass the cfg
cfg.trialdef.eventtype  = 'Stimulus';
cfg.trialdef.eventvalue = {'S200' 'S201' 'S202'};           % read all conditions at once
cfg.trialdef.prestim    = -2.0; % in seconds
cfg.trialdef.poststim   = 2.0; % in seconds

cfg = ft_definetrial(cfg);
cfg.channel = 'all';

cfg.demean = 'yes';
cfg.baselinewindow = [-0.2 0.0];

cfg.dftfilter = 'yes';
cfg.dftfreq = [50 60];

prepped_data= ft_preprocessing(cfg);

end

