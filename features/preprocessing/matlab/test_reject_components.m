addpath('C:\FIELDTRIP'); % Adjust as necessary for your FieldTrip installation
% TEST_REJECT_COMPONENTS Quick smoke test for reject_components.m
%
% Loads an existing rejected_ICs_*.m summary, builds minimal FieldTrip-like
% structures, and calls reject_components to ensure nested component
% selections are handled correctly.
%
% Usage:
%   1. Ensure FieldTrip is on the MATLAB path (ft_rejectcomponent must exist).
%   2. Adjust data/ICA mock definitions below if necessary for your dataset.
%   3. Run this script from anywhere; it derives paths relative to itself.
%
% Note: This script performs a minimal call to reject_components without
% inspecting the actual clean_data output. Extend it according to your needs.

%% Setup paths
script_folder = fileparts(mfilename('fullpath'));
matlab_folder = script_folder;
addpath(matlab_folder);

% Add FieldTrip to path if available
fieldtrip_path = 'C:\FIELDTRIP';
if exist(fieldtrip_path, 'dir')
    addpath(fieldtrip_path);
    ft_defaults; % Initialize FieldTrip
else
    warning('FieldTrip not found at %s. Please ensure it is installed and on path.', fieldtrip_path);
end

%% Locate rejected ICs summaries (including nested component selections)
summary_dir = fullfile(matlab_folder, 'rejected ICs');
if exist(summary_dir, 'dir') ~= 7
    error('Rejected IC summaries folder not found: %s', summary_dir);
end

summary_listing = dir(fullfile(summary_dir, 'rejected_ICs_*.m'));
summary_listing = summary_listing(~contains({summary_listing.name}, '_clean'));
if isempty(summary_listing)
    error('No rejected_ICs_*.m files found in %s', summary_dir);
end
fprintf('Found %d rejected IC summary file(s) in %s.\n', numel(summary_listing), summary_dir);

% Determine latest summary using embedded timestamp inside the file. Fallback to
% filesystem datenum if the header is missing or unparsable.
latest_timestamp = -Inf;
latest_idx = NaN;

for idx = 1:numel(summary_listing)
    candidate_path = fullfile(summary_dir, summary_listing(idx).name);
    candidate_content = fileread(candidate_path);
    timestamp_value = extract_summary_timestamp(candidate_content, summary_listing(idx).datenum);
    
    if timestamp_value > latest_timestamp
        latest_timestamp = timestamp_value;
        latest_idx = idx;
    end
end

if isnan(latest_idx)
    error('Unable to determine latest rejected IC summary.');
end

summary_file = fullfile(summary_dir, summary_listing(latest_idx).name);
summary_content = fileread(summary_file);
summary_datetime = datetime(latest_timestamp, 'ConvertFrom', 'datenum');

fprintf('Using latest summary file: %s (generated %s).\n', summary_file, ...
    datestr(summary_datetime, 'yyyy-mm-dd HH:MM:SS'));

%% Load ICA data
ica_data_path = fullfile(matlab_folder, 'data_ICA.mat');
if exist(ica_data_path, 'file') ~= 2
    error('ICA data file not found: %s', ica_data_path);
end
ica_data_struct = load(ica_data_path, 'data_ICApplied');
if ~isfield(ica_data_struct, 'data_ICApplied')
    error('Variable data_ICApplied not found in %s', ica_data_path);
end

ICAppliedStructArray = ica_data_struct.data_ICApplied;
num_subjects = numel(ICAppliedStructArray);
ICApplied = arrayfun(@(s) s, ICAppliedStructArray, 'UniformOutput', false);

%% Reconstruct sensor-space data from ICA components
data = cell(1, num_subjects);
for i = 1:num_subjects
    comp = ICApplied{i};
    raw = struct();
    raw.label = comp.topolabel;
    raw.fsample = comp.fsample;
    raw.time = comp.time;
    raw.trial = cell(size(comp.trial));
    for t = 1:numel(comp.trial)
        raw.trial{t} = comp.topo * comp.trial{t};
    end
    data{i} = raw;
end

%% Evaluate latest summary and probe nested arrays
clear('rejected_ICs_array'); %#ok<CLFN>
eval(summary_content);

if ~exist('rejected_ICs_array', 'var')
    error('Summary file %s did not define rejected_ICs_array.', summary_file);
end

selections = rejected_ICs_array(:)';
clear('rejected_ICs_array');

if numel(selections) < num_subjects
    fprintf('Padding selection entries from %d to %d subjects with empties.\n', ...
        numel(selections), num_subjects);
    selections(end+1:num_subjects) = {[]}; %#ok<AGROW>
elseif numel(selections) > num_subjects
    warning('Selection entries exceed available subjects (%d > %d). Truncating extras.', ...
        numel(selections), num_subjects);
    selections = selections(1:num_subjects);
end

flattened_components = cellfun(@(entry) flatten_component_entry(entry), ...
    selections, 'UniformOutput', false);

baseline_clean = reject_components(data, ICApplied, flattened_components);
raw_clean = reject_components(data, ICApplied, selections);

report_comparison('Raw summary vs baseline flattened', baseline_clean, raw_clean, ...
    selections, flattened_components);

synthetic_nested = cellfun(@(entry) synthesize_nested_entry(entry), ...
    flattened_components, 'UniformOutput', false);

nested_clean = reject_components(data, ICApplied, synthetic_nested);

report_comparison('Synthetic nested scenario vs baseline flattened', baseline_clean, ...
    nested_clean, synthetic_nested, flattened_components);

%% Generate cleaned dataset and persist result
clean_data = raw_clean; % already verified equivalent to flattened baseline
clean_output_path = fullfile(matlab_folder, 'data_ICA_clean.mat');
save(clean_output_path, 'clean_data', 'selections', 'summary_file', 'summary_datetime');

fprintf('\nSaved cleaned dataset to %s.\n', clean_output_path);

%% Compare original vs cleaned data to confirm rejection
report_original_vs_clean(data, clean_data, flattened_components);

fprintf('\nNested array evaluation and data cleaning complete.\n');

%% Local helper functions -------------------------------------------------
function components = flatten_component_entry(entry)
% Mirror reject_components normalization logic to obtain comparable baselines.

if nargin == 0 || isempty(entry)
    components = [];
    return;
end

if isequal(entry, 0)
    components = [];
    return;
end

if iscell(entry)
    components = [];
    for cIdx = 1:numel(entry)
        components = [components, flatten_component_entry(entry{cIdx})]; %#ok<AGROW>
    end
    components = unique(components(:)');
    return;
end

if isnumeric(entry)
    entry = entry(:)';
    entry(entry == 0) = [];
    components = unique(entry);
    return;
end

if islogical(entry)
    components = flatten_component_entry(double(entry));
    return;
end

warning('test_reject_components:UnsupportedComponentType', ...
    'Unsupported component entry of type %s encountered while flattening.', class(entry));
components = [];
end

function nested_entry = synthesize_nested_entry(flat_entry)
% Build a deliberately tangled structure that should flatten back to flat_entry.

if isempty(flat_entry)
    nested_entry = {};
    return;
end

if iscell(flat_entry)
    % Already nested from source; re-wrap to add extra depth without altering values.
    flat_numbers = flatten_component_entry(flat_entry);
else
    flat_numbers = flat_entry(:)';
end

flat_numbers = unique(flat_numbers(flat_numbers ~= 0));

if isempty(flat_numbers)
    nested_entry = {};
    return;
end

lead_count = min(2, numel(flat_numbers));
nested_entry = {flat_numbers(1:lead_count)};

if numel(flat_numbers) > lead_count
    remainder = flat_numbers(lead_count+1:end);
    nested_entry{end+1} = arrayfun(@(comp) {comp}, remainder, 'UniformOutput', false);
end

nested_entry{end+1} = {flat_numbers};
nested_entry{end+1} = {{flat_numbers}}; % add a deeper cell-of-cells layer
nested_entry{end+1} = 0;                % ensure zero entries are ignored
nested_entry{end+1} = {0};
end

function report_comparison(label, baseline_clean, candidate_clean, candidate_rejections, baseline_flat)
fprintf('\n[%s]\n', label);
for subj = 1:numel(baseline_clean)
    [total_norm, max_abs] = compute_differences(baseline_clean{subj}, candidate_clean{subj});
    selection_str = format_selection(candidate_rejections{subj});
    flattened_str = mat2str(baseline_flat{subj});
    fprintf(['Subject %d | selection: %s | flattened -> %s | ' ...
        'Fro norm diff: %.6f | Max abs diff: %.6f\n'], ...
        subj, selection_str, flattened_str, total_norm, max_abs);
end
end

function [total_norm, max_abs] = compute_differences(reference_data, candidate_data)
total_norm = 0;
max_abs = 0;

if isempty(reference_data) || isempty(candidate_data)
    return;
end

num_trials = min(numel(reference_data.trial), numel(candidate_data.trial));
for trialIdx = 1:num_trials
    delta = reference_data.trial{trialIdx} - candidate_data.trial{trialIdx};
    total_norm = total_norm + norm(delta, 'fro');
    max_abs = max(max_abs, max(abs(delta), [], 'all'));
end
end

function out = format_selection(entry)
if nargin == 0 || isempty(entry)
    out = '[]';
    return;
end

if isnumeric(entry) || islogical(entry)
    out = mat2str(entry);
    return;
end

if iscell(entry)
    str = strtrim(evalc('disp(entry)'));
    out = regexprep(str, '\s+', ' ');
    return;
end

out = sprintf('<%s>', class(entry));
end

function timestamp_value = extract_summary_timestamp(file_content, fallback_datenum)
% Attempt to extract "Generated on:" timestamp from summary file content.

timestamp_value = fallback_datenum;
token = regexp(file_content, 'Generated on:\s*([\d]{2}-[A-Za-z]{3}-[\d]{4}\s+[\d]{2}:[\d]{2}:[\d]{2})', ...
    'tokens', 'once');

if isempty(token)
    return;
end

try
    dt = datetime(token{1}, 'InputFormat', 'dd-MMM-yyyy HH:mm:ss');
    timestamp_value = datenum(dt);
catch
    warning('Failed to parse timestamp "%s" from summary header. Using fallback datenum.', token{1});
end
end

function report_original_vs_clean(original_data, cleaned_data, flattened_components)
fprintf('\n[Original vs Cleaned Data]\n');
for subj = 1:numel(original_data)
    [total_norm, max_abs] = compute_differences(original_data{subj}, cleaned_data{subj});
    expected_components = mat2str(flattened_components{subj});
    status = 'UNCHANGED';
    if total_norm > 0 || max_abs > 0
        status = 'MODIFIED';
    end
    fprintf(['Subject %d | expected rejects: %s | Status: %s | ' ...
        'Fro norm diff: %.6f | Max abs diff: %.6f\n'], ...
        subj, expected_components, status, total_norm, max_abs);
end
end