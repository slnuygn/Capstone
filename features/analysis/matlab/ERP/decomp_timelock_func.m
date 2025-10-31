function ERP_data = decomp_timelock_func(inputPath)
% decomposition for cleaned ICA data stored as data_ICApplied_clean.mat

if nargin < 1 || isempty(inputPath)
    error('decomp_timelock_func requires a folder path containing data_ICApplied_clean.mat.');
end

% Resolve folder and target file
if isfolder(inputPath)
    dataFolder = inputPath;
else
    [dataFolder, fileName, fileExt] = fileparts(inputPath);
    if isempty(dataFolder)
        dataFolder = pwd;
    end
    if ~strcmpi([fileName fileExt], 'data_ICApplied_clean.mat')
        fprintf('Input path is a file (%s %s). Using containing folder: %s\n', fileName, fileExt, dataFolder);
    end
end

matFilePath = fullfile(dataFolder, 'data_ICApplied_clean.mat');
fprintf('Loading data from: %s\n', matFilePath);

if ~exist(matFilePath, 'file')
    error('Required file data_ICApplied_clean.mat not found in %s', dataFolder);
end

% Load the cleaned data variable saved by browse_ICA
try
    loadedData = load(matFilePath, 'clean_data');
catch loadErr
    error('Failed to load data_ICApplied_clean.mat: %s', loadErr.message);
end

if ~isfield(loadedData, 'clean_data')
    error('Variable "clean_data" not found inside data_ICApplied_clean.mat.');
end

data_ICApplied_clean = loadedData.clean_data;
fprintf('Successfully loaded clean_data from data_ICApplied_clean.mat\n');

% Normalize loaded data to a cell array so downstream code can use brace indexing
fprintf('Examining data structure...\n');
if iscell(data_ICApplied_clean)
    fprintf('data_ICApplied_clean is a cell array with %d elements\n', length(data_ICApplied_clean));
    data_ICApplied_clean = data_ICApplied_clean(:);
elseif isstruct(data_ICApplied_clean)
    fprintf('data_ICApplied_clean is a struct array with %d element(s)\n', numel(data_ICApplied_clean));
    if numel(data_ICApplied_clean) == 1
        data_ICApplied_clean = {data_ICApplied_clean};
    else
        data_ICApplied_clean = num2cell(data_ICApplied_clean(:));
    end
else
    error('Unsupported data type for data_ICApplied_clean: %s', class(data_ICApplied_clean));
end

if isempty(data_ICApplied_clean)
    error('data_ICApplied_clean is empty after normalization.');
end

first_elem = data_ICApplied_clean{1};
fprintf('First element type after normalization: %s\n', class(first_elem));
if isstruct(first_elem)
    fprintf('First element fields: %s\n', strjoin(fieldnames(first_elem), ', '));
    if isfield(first_elem, 'trialinfo')
        sample_len = min(5, numel(first_elem.trialinfo));
        fprintf('trialinfo sample: %s\n', mat2str(first_elem.trialinfo(1:sample_len)));
    else
        fprintf('trialinfo field does NOT exist on first element\n');
    end
elseif isnumeric(first_elem)
    fprintf('First element is numeric array, size: %s\n', mat2str(size(first_elem)));
else
    fprintf('First element is of type: %s\n', class(first_elem));
end

numTrials = numel(data_ICApplied_clean);
fprintf('Number of trials: %d\n', numTrials);

% Initialize FieldTrip if not already done
if ~exist('ft_defaults', 'file')
    fprintf('FieldTrip not found, attempting to initialize...\n');
    % Try to find FieldTrip in common locations
    ft_paths = {
        'C:\Program Files\MATLAB\fieldtrip';  % Default MATLAB installation
        'C:\fieldtrip';  % Alternative location
        'D:\fieldtrip';  % Another possible location
        fullfile(userpath, 'fieldtrip')  % User path
        };
    
    ft_found = false;
    for i = 1:length(ft_paths)
        ft_path = ft_paths{i};
        if exist(ft_path, 'dir')
            fprintf('Found FieldTrip at: %s\n', ft_path);
            addpath(ft_path);
            try
                ft_defaults;
                fprintf('FieldTrip initialized successfully\n');
                ft_found = true;
                break;
            catch
                fprintf('Failed to initialize FieldTrip from: %s\n', ft_path);
                rmpath(ft_path);
            end
        end
    end
    
    if ~ft_found
        error(['FieldTrip not found. Please install FieldTrip and ensure it is on MATLAB path.\n' ...
            'Common installation locations:\n' ...
            '- C:\\Program Files\\MATLAB\\fieldtrip\n' ...
            '- C:\\fieldtrip\n' ...
            '- Your MATLAB userpath/fieldtrip\n' ...
            'Or add FieldTrip to MATLAB path manually.']);
    end
else
    fprintf('FieldTrip already initialized\n');
end

data_ICApplied_clean_decomp = struct( ...
    'target_data', cell(1, numTrials), ...
    'standard_data', cell(1, numTrials), ...
    'novelty_data', cell(1, numTrials));

fprintf('Starting decomposition...\n');
for i = 1:numTrials
    fprintf('Processing trial %d/%d\n', i, numTrials);
    
    % Debug: examine what we're passing to decompose
    fprintf('Examining data_ICApplied_clean{%d}:\n', i);
    trial_data = data_ICApplied_clean{i};
    fprintf('Type: %s\n', class(trial_data));
    if iscell(trial_data)
        fprintf('Cell array with %d elements\n', length(trial_data));
        if length(trial_data) > 0
            fprintf('First element type: %s\n', class(trial_data{1}));
        end
    elseif isstruct(trial_data)
        fprintf('Struct with fields: %s\n', strjoin(fieldnames(trial_data), ', '));
        if isfield(trial_data, 'trialinfo')
            fprintf('Has trialinfo field\n');
        else
            fprintf('Missing trialinfo field\n');
        end
    else
        fprintf('Other type: %s\n', class(trial_data));
    end
    
    [data_ICApplied_clean_decomp(i).target_data, ...
        data_ICApplied_clean_decomp(i).standard_data, ...
        data_ICApplied_clean_decomp(i).novelty_data] = decompose(data_ICApplied_clean{i});
end
fprintf('Decomposition completed\n');

% time lock analysis
fprintf('Starting timelock analysis...\n');
ERP_data = struct( ...
    'target', cell(1, numTrials), ...
    'standard', cell(1, numTrials), ...
    'novelty', cell(1, numTrials));

for i = 1:numTrials
    fprintf('Timelock analysis for trial %d/%d\n', i, numTrials);
    cfg = [];
    cfg.latency = [0 1];
    
    ERP_data(i).target = ft_timelockanalysis(cfg, data_ICApplied_clean_decomp(i).target_data);
    ERP_data(i).standard = ft_timelockanalysis(cfg, data_ICApplied_clean_decomp(i).standard_data);
    ERP_data(i).novelty = ft_timelockanalysis(cfg, data_ICApplied_clean_decomp(i).novelty_data);
end
fprintf('Timelock analysis completed\n');

%% separate into classes and extract the ERP data (avg)
% for now commenting out the code without deleting it
% For old group
%old_target = extract_erp_data(ERP_data, 'target');
%old_standard = extract_erp_data(ERP_data, 'standard');
%old_novelty = extract_erp_data(ERP_data, 'novelty');

outputPath = fullfile(dataFolder, 'erp_output.mat');
save(outputPath, 'ERP_data');
fprintf('ERP analysis results saved to %s\n', outputPath);
end
