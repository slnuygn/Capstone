% check out https://www.fieldtriptoolbox.org/tutorial/connectivity/connectivity_aef/#connectivity-analysis

cfg        = [];
cfg.numtrl = 100
data       = ft_freqsimulation(cfg); % simulate some data

cfg        = [];
cfg.method = 'wavelet';
cfg.toi    = 0:0.01:1;
cfg.output = 'fourier';
freq       = ft_freqanalysis(cfg, data);

% make a new FieldTrip-style data structure containing the ITC
% copy the descriptive fields over from the frequency decomposition

itc           = [];
itc.label     = freq.label;
itc.freq      = freq.freq;
itc.time      = freq.time;
itc.dimord    = 'chan_freq_time';

F = freq.fourierspctrm;   % copy the Fourier spectrum
N = size(F,1);           % number of trials

% compute inter-trial phase coherence (itpc)
itc.itpc      = F./abs(F);         % divide by amplitude
itc.itpc      = sum(itc.itpc,1);   % sum angles
itc.itpc      = abs(itc.itpc)/N;   % take the absolute value and normalize
itc.itpc      = squeeze(itc.itpc); % remove the first singleton dimension

% compute inter-trial linear coherence (itlc)
itc.itlc      = sum(F) ./ (sqrt(N*sum(abs(F).^2)));
itc.itlc      = abs(itc.itlc);     % take the absolute value, i.e. ignore phase
itc.itlc      = squeeze(itc.itlc); % remove the first singleton dimension