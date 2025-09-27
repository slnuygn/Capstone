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
    
    % Initialize rejected ICs array - zeros array with same size as ICA_data
    rejected_ICs_array = cell(length(ICA_data), 1);
    for j = 1:length(ICA_data)
        rejected_ICs_array{j} = [];  % Initialize as empty array for each subject
    end
    
    % Browse the ICA components
    for i = 1:length(ICA_data)
        cfg = [];
        cfg.allowoverlap = 'yes';
        cfg.layout = 'easycapM11.lay';  % your layout file
        cfg.viewmode = 'component';      % component view mode
        cfg.continuous = 'no';
        cfg.total_subjects = length(ICA_data);  % Pass total subject count
        cfg.current_subject_index = i;  % Pass current subject index
        
        fprintf('Showing components for subject %d\n', i);
        
        % Call ft_databrowser and wait for it to complete
        cfg_out = ft_databrowser(cfg, ICA_data(i));
        
        % Collect rejected ICs for current subject
        if isfield(cfg_out, 'rejected_ICs') && ~isempty(cfg_out.rejected_ICs)
            % Since we're processing one subject at a time, the rejected_ICs
            % should contain data for the current subject at index i
            subject_rejected = [];
            
            if i <= length(cfg_out.rejected_ICs)
                current_subject_data = cfg_out.rejected_ICs{i};
                
                if isequal(current_subject_data, 0)
                    subject_rejected = [];  % No rejected components
                elseif iscell(current_subject_data)
                    subject_rejected = cell2mat(current_subject_data);
                else
                    subject_rejected = current_subject_data;
                end
            end
            
            rejected_ICs_array{i} = subject_rejected;
        else
            rejected_ICs_array{i} = [];  % No rejected components
        end
        
        % Display what was rejected for this subject
        if isempty(rejected_ICs_array{i})
            fprintf('Subject %d: No components rejected\n', i);
        else
            fprintf('Subject %d: Rejected components [%s]\n', i, num2str(rejected_ICs_array{i}));
        end
        
        % Wait for user input to proceed to next subject (except for the last one)
        if i < length(ICA_data)
            fprintf('Subject %d processing complete. Press any key to continue to subject %d...\n', i, i+1);
            pause;
            % Close the current figure before opening the next one
            if ishandle(gcf)
                close(gcf);
            end
        end
    end
    
    % Display final results
    fprintf('\n=== Final Rejected Components Summary ===\n');
    for i = 1:length(rejected_ICs_array)
        if isempty(rejected_ICs_array{i})
            fprintf('Subject %d: No components rejected\n', i);
        else
            fprintf('Subject %d: Rejected components [%s]\n', i, num2str(rejected_ICs_array{i}));
        end
    end
    
    % Save results to workspace
    assignin('base', 'rejected_ICs_array', rejected_ICs_array);
    fprintf('\nRejected components array saved to workspace as "rejected_ICs_array"\n');
    
    % Save results to a script file
    timestamp = datestr(now, 'yyyy-mm-dd_HH-MM-SS');
    script_filename = sprintf('rejected_ICs_%s.m', timestamp);
    
    fid = fopen(script_filename, 'w');
    if fid ~= -1
        % Write header
        fprintf(fid, '%% Rejected ICA Components Results\n');
        fprintf(fid, '%% Generated on: %s\n', datestr(now));
        fprintf(fid, '%% Source file: %s\n', mat_file_path);
        fprintf(fid, '%% Total subjects: %d\n\n', length(rejected_ICs_array));
        
        % Write the array
        fprintf(fid, 'rejected_ICs_array = {\n');
        for i = 1:length(rejected_ICs_array)
            if isempty(rejected_ICs_array{i})
                fprintf(fid, '    []; %% Subject %d: No rejected components\n', i);
            else
                fprintf(fid, '    [%s]; %% Subject %d: Rejected components\n', num2str(rejected_ICs_array{i}), i);
            end
        end
        fprintf(fid, '};\n\n');
        
        % Write summary comments
        total_subjects_with_rejections = sum(~cellfun(@isempty, rejected_ICs_array));
        total_rejections = sum(cellfun(@length, rejected_ICs_array));
        
        fprintf(fid, '%% Summary:\n');
        fprintf(fid, '%% Total subjects: %d\n', length(rejected_ICs_array));
        fprintf(fid, '%% Subjects with rejections: %d\n', total_subjects_with_rejections);
        fprintf(fid, '%% Total components rejected: %d\n', total_rejections);
        
        fclose(fid);
        fprintf('Results saved to script file: %s\n', script_filename);
    else
        fprintf('Warning: Could not create script file %s\n', script_filename);
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