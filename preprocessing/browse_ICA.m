function browse_ICA(mat_file_path)
% Function to browse ICA components from a .mat file
% Input: mat_file_path - path to the .mat file containing ICA data

set(groot, 'DefaultFigureColormap', jet);

try
    % Load the .mat file
    fprintf('Loading file: %s\n', mat_file_path);
    loaded_data = load(mat_file_path);
    
    % Display what variables we found
    var_names = fieldnames(loaded_data);
    fprintf('Variables in file: %s\n', strjoin(var_names, ', '));
    
    % Try to find ICA data variable automatically
    ICA_data = [];
    var_used = '';
    
    % Get all non-metadata variable names
    var_names = fieldnames(loaded_data);
    data_vars = {};
    for j = 1:length(var_names)
        if length(var_names{j}) < 2 || ~strcmp(var_names{j}(1:2), '__')
            data_vars{end+1} = var_names{j};
        end
    end
    
    fprintf('Searching for ICA data in %d variables...\n', length(data_vars));
    
    % Look for variables that contain ICA data structures
    for i = 1:length(data_vars)
        var_name = data_vars{i};
        var_data = loaded_data.(var_name);
        
        fprintf('Checking variable: %s\n', var_name);
        
        % Check if this variable looks like ICA data
        if isICAData(var_data)
            ICA_data = var_data;
            var_used = var_name;
            fprintf('Found ICA data in variable: %s\n', var_name);
            break;
        end
    end
    
    if isempty(ICA_data)
        error('No suitable ICA data variable found in file');
    end
    
    fprintf('Using variable: %s\n', var_used);
    fprintf('Data contains %d subject(s)\n', length(ICA_data));
    
    % Browse the ICA components
    for i = 1:length(ICA_data)
        cfg = [];
        cfg.allowoverlap = 'yes';
        cfg.layout = 'easycapM11.lay';  % your layout file
        cfg.viewmode = 'component';      % component view mode
        cfg.continuous = 'no';
        cfg.total_subjects = length(ICA_data);  % Pass total subject count
        
        fprintf('Showing components for subject %d\n', i);
        ft_databrowser(cfg, ICA_data(i));
        
        % Optional: wait for user input to proceed to next subject
        if length(ICA_data) > 1
            pause;  % waits for keypress before continuing to next subject
        end
    end
    
    fprintf('ICA component browsing completed.\n');
    
catch ME
    fprintf('Error in browse_ICA: %s\n', ME.message);
    fprintf('Stack trace:\n');
    for i = 1:length(ME.stack)
        fprintf('  %s (line %d)\n', ME.stack(i).name, ME.stack(i).line);
    end
end

    function is_ica = isICAData(data)
        % Helper function to determine if a variable contains ICA data
        % Returns true if the data structure looks like FieldTrip ICA data
        
        is_ica = false;
        
        fprintf('  -> Checking data type: %s\n', class(data));
        
        % Check if it's a structure
        if ~isstruct(data)
            fprintf('  -> Not a struct\n');
            return;
        end
        
        fprintf('  -> Is a struct\n');
        
        % Check for basic FieldTrip fields
        if isfield(data, 'label')
            fprintf('  -> Has label field\n');
        else
            fprintf('  -> Missing label field\n');
        end
        
        if isfield(data, 'trial')
            fprintf('  -> Has trial field\n');
        else
            fprintf('  -> Missing trial field\n');
        end
        
        if isfield(data, 'time')
            fprintf('  -> Has time field\n');
        else
            fprintf('  -> Missing time field\n');
        end
        
        % If it has basic FieldTrip structure, consider it ICA data
        if isfield(data, 'label') && isfield(data, 'trial') && isfield(data, 'time')
            fprintf('  -> Has basic FieldTrip structure - assuming ICA data\n');
            is_ica = true;
        else
            fprintf('  -> Missing required FieldTrip fields\n');
        end
    end

end