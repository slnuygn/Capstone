% Initialize FieldTrip
addpath('C:/FIELDTRIP');  % Replace with your FieldTrip path
ft_defaults;

% Set the directory containing the .set files
data_dir = 'file:///C:/Users/mamam/Desktop/data';  % Will be updated by the GUI file browser when folder is selected

% Get the preprocessing script directory and add to path
preprocessing_dir = fileparts(mfilename('fullpath'));
addpath(preprocessing_dir);

% Change to data directory to find .set files
cd(data_dir);
files = dir('*.set');

accepted_channels = {'F4', 'Fz', 'C3', 'Pz', 'P3', 'O1', 'Oz', 'O2', 'P4', 'Cz', 'C4', 'F3'};

% Loop through each .set file
for i = 1:length(files)
    
    filename = files(i).name;
    fprintf('Processing %s...\n', filename);
    
    % Load the data
    dataset = fullfile(data_dir, filename);
    
    % Process the data - this automatically stores in MATLAB workspace
    data(i) = preprocess_data(dataset, accepted_channels);
    
end

fprintf('Batch processing complete. %d files processed and stored in workspace variable "data"\n', length(data));

% Apply ICA to the preprocessed data
fprintf('Applying ICA to preprocessed data...\n');
data_ICApplied = applyICA(data);
fprintf('ICA processing complete.\n');

% Save the final ICA-processed data
output_filename = fullfile(data_dir, 'data_ICA.mat');
save(output_filename, 'data_ICApplied');
fprintf('Final ICA-processed data saved to: %s\n', output_filename);

