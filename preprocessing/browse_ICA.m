set(groot, 'DefaultFigureColormap', jet);

for i = 1:length(old_ICApplied)
    cfg = [];
    cfg.allowoverlap = 'yes';
    cfg.layout    = 'easycapM11.lay';             % your layout file
    cfg.viewmode  = 'component'; % could also be component
    cfg.continuous = 'no';
    
    fprintf('Showing components for subject %d\n', i);
    ft_databrowser(cfg, old_ICApplied(i));
    
    % Optional: wait for user input to proceed to next subject
    pause;  % waits for keypress before continuing
end