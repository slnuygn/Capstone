% 1. Load the preprocessed task data (as shown in Part I)
% This file presumably contains the 'data_visc' and 'data_audc' variables.
load('/madrid2019/tutorial_freq/data_task.mat');

% 2. Define the configuration for spectral analysis (inspired by Part II)
cfg = [];
cfg.output = 'pow';        % We want to compute the power spectrum
cfg.channel = 'all';
cfg.method = 'mtmfft';     % Specify 'mtmfft' for spectral analysis (FFT)
cfg.taper = 'hanning';   % Use a Hanning taper (a good single taper, as used in Part II)
cfg.foi = 1:1:30;        % Frequencies of interest (e.g., 1 to 30 Hz in 1 Hz steps)

% 3. Run the spectral analysis on the task data variables
% This will compute the average power spectrum across all trials
pow_visc = ft_freqanalysis(cfg, data_visc);
pow_audc = ft_freqanalysis(cfg, data_audc);

% 4. (Optional) Visualize the results
% You can use ft_multiplotER or ft_singleplotER to view the spectra

figure;
cfg_plot = [];
cfg_plot.layout = 'easycapM10.mat'; % Specify the layout file used in the tutorial
ft_multiplotER(cfg_plot, pow_visc, pow_audc);
legend('Visual', 'Auditory');

figure;
cfg_plot.channel = '1'; % Plot a single channel (e.g., channel '1')
ft_singleplotER(cfg_plot, pow_visc, pow_audc);
legend('Visual', 'Auditory');
xlabel('Frequency (Hz)');
ylabel('Power');