function [clean_data] = reject_components(data, ICApplied, rejected_comps)
% REJECT_COMPONENTS Rejects components from data based on ICA results
%   [clean_data] = reject_components(data, ICApplied, rejected_comps)
%
% Inputs:
%   data - Cell or struct array of raw data structures
%   ICApplied - Cell or struct array of ICA results
%   rejected_comps - Cell array or numeric matrix/vector of components to reject
%
% Outputs:
%   clean_data - Cleaned data matching the input container type (hdr preserved)

data_is_cell = iscell(data);
ica_is_cell = iscell(ICApplied);

num_records = numel(data);

if num_records == 0
    clean_data = data;
    return;
end

if nargin < 3 || isempty(rejected_comps)
    rejected_comps = cell(1, num_records);
else
    rejected_comps = normalize_selection_container(rejected_comps, num_records);
end

clean_cells = cell(1, num_records);
forbidden_fields = {'topo', 'unmixing', 'topolabel'};
fields_to_transfer = {'label', 'time', 'trial', 'fsample', 'sampleinfo', 'trialinfo', 'cfg'};
field_union = determine_field_union(data, forbidden_fields);
field_union = union(field_union, fields_to_transfer, 'stable');

for idx = 1:num_records
    current_data = fetch_entry(data, data_is_cell, idx, 'data');
    current_ica = fetch_entry(ICApplied, ica_is_cell, idx, 'ICApplied');
    
    components_to_reject = [];
    if idx <= numel(rejected_comps)
        components_to_reject = normalize_components(rejected_comps{idx});
    end
    
    if isempty(components_to_reject)
        updated_data = current_data;
    else
        cfg = [];
        cfg.component = components_to_reject;
        updated_data = ft_rejectcomponent(cfg, current_ica, current_data);
    end
    
    cleaned_entry = current_data; % direct copy preserves hdr and metadata
    if isstruct(updated_data)
        for fIdx = 1:numel(fields_to_transfer)
            field_name = fields_to_transfer{fIdx};
            if isfield(updated_data, field_name)
                cleaned_entry.(field_name) = updated_data.(field_name);
            end
        end
    end
    
    cleaned_entry = remove_forbidden_fields(cleaned_entry, forbidden_fields);
    cleaned_entry.rejected_components = components_to_reject(:)';
    cleaned_entry = ensure_field_set(cleaned_entry, field_union);
    clean_cells{idx} = cleaned_entry;
end

% Ensure every entry exposes hdr directly; fallback to extraction if missing
for idx = 1:num_records
    target_entry = clean_cells{idx};
    if (~isfield(target_entry, 'hdr') || isempty(target_entry.hdr))
        recovered_hdr = extract_hdr_metadata(target_entry);
        if isempty(recovered_hdr)
            original_entry = fetch_entry(data, data_is_cell, idx, 'data');
            recovered_hdr = extract_hdr_metadata(original_entry);
        end
        if ~isempty(recovered_hdr)
            target_entry.hdr = recovered_hdr;
            clean_cells{idx} = target_entry;
        end
    end
end

clean_cells = equalize_struct_fields(clean_cells, field_union);

if data_is_cell
    clean_data = clean_cells;
else
    if isempty(clean_cells)
        clean_data = struct([]);
    else
        clean_data = [clean_cells{:}];
    end
end
end

function components = normalize_components(entry)
% NORMALIZE_COMPONENTS Flatten and clean component selections for rejection
%   Ensures that nested cell arrays and zero/empty markers are handled.

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
    for idx = 1:numel(entry)
        components = [components, normalize_components(entry{idx})]; %#ok<AGROW>
    end
    components = unique(components(:)');
    return;
end

if isnumeric(entry)
    entry = entry(:)';
    entry(~isfinite(entry)) = [];
    entry(entry == 0) = [];
    components = unique(entry);
    return;
end

if islogical(entry)
    components = normalize_components(double(entry));
    return;
end

warning('reject_components:UnsupportedComponentType', ...
    'Unsupported component selection of type %s. Ignoring.', class(entry));
components = [];
end

function entries = normalize_selection_container(selection, target_len)
if iscell(selection)
    entries = selection;
else
    numeric_selection = selection;
    entries = cell(1, target_len);
    if ~isempty(numeric_selection)
        if size(numeric_selection, 1) == target_len
            for k = 1:target_len
                entries{k} = numeric_selection(k, :);
            end
        else
            linear = numeric_selection(:)';
            for k = 1:target_len
                if k <= numel(linear)
                    entries{k} = linear(k);
                else
                    entries{k} = [];
                end
            end
        end
    end
end

if numel(entries) < target_len
    entries(end+1:target_len) = {[]}; %#ok<AGROW>
elseif numel(entries) > target_len
    warning('reject_components:SelectionLengthMismatch', ...
        'Received %d rejection entries for %d records. Truncating extras.', ...
        numel(entries), target_len);
    entries = entries(1:target_len);
end
end

function entry = fetch_entry(container, is_cell, index, argument_name)
if is_cell
    if index > numel(container)
        error('reject_components:LengthMismatch', ...
            'Not enough entries in %s (expected at least %d).', argument_name, index);
    end
    entry = container{index};
else
    if index > numel(container)
        error('reject_components:LengthMismatch', ...
            'Not enough entries in %s (expected at least %d).', argument_name, index);
    end
    entry = container(index);
end
end

function entry = remove_forbidden_fields(entry, forbidden_fields)
if ~isstruct(entry) || isempty(forbidden_fields)
    return;
end

for idx = 1:numel(forbidden_fields)
    field_name = forbidden_fields{idx};
    if isfield(entry, field_name)
        entry = rmfield(entry, field_name);
    end
end
end

function hdr_value = extract_hdr_metadata(entry)
hdr_value = [];
if nargin == 0 || isempty(entry)
    return;
end

max_depth = 10;
queue = {entry};
depths = 0;
visited = cell(0, 1);

while ~isempty(queue)
    current = queue{1};
    queue(1) = [];
    current_depth = depths(1);
    depths(1) = [];
    
    if isempty(current)
        continue;
    end
    
    if iscell(current)
        for cellIdx = 1:numel(current)
            queue{end+1} = current{cellIdx}; %#ok<AGROW>
            depths(end+1) = current_depth; %#ok<AGROW>
        end
        continue;
    end
    
    if ~isstruct(current)
        continue;
    end
    
    if any(cellfun(@(s) isequal(s, current), visited))
        continue;
    end
    visited{end+1, 1} = current; %#ok<AGROW>
    
    if isfield(current, 'hdr') && ~isempty(current.hdr)
        hdr_value = current.hdr;
        return;
    end
    
    if current_depth >= max_depth
        continue;
    end
    
    next_depth = current_depth + 1;
    
    if isfield(current, 'previous')
        queue{end+1} = current.previous; %#ok<AGROW>
        depths(end+1) = next_depth; %#ok<AGROW>
    end
    
    if isfield(current, 'raw')
        queue{end+1} = current.raw; %#ok<AGROW>
        depths(end+1) = next_depth; %#ok<AGROW>
    end
    
    if isfield(current, 'cfg')
        queue{end+1} = current.cfg; %#ok<AGROW>
        depths(end+1) = next_depth; %#ok<AGROW>
    end
end
end

function field_union = determine_field_union(container, forbidden_fields)
field_union = {};
if iscell(container)
    entries = container;
elseif isstruct(container)
    entries = num2cell(container);
else
    entries = {};
end

for idx = 1:numel(entries)
    entry = entries{idx};
    if ~isstruct(entry)
        continue;
    end
    fields = setdiff(fieldnames(entry), forbidden_fields, 'stable');
    field_union = union(field_union, fields, 'stable');
end

field_union = union(field_union, {'rejected_components'}, 'stable');
if ~ismember('hdr', field_union)
    field_union = union(field_union, {'hdr'}, 'stable');
end
end

function entry = ensure_field_set(entry, field_names)
if ~isstruct(entry)
    return;
end

for idx = 1:numel(field_names)
    field_name = field_names{idx};
    if ~isfield(entry, field_name)
        entry.(field_name) = [];
    end
end
end

function container = equalize_struct_fields(container, field_union)
if isempty(field_union)
    return;
end

if iscell(container)
    for idx = 1:numel(container)
        if isstruct(container{idx})
            container{idx} = ensure_field_set(container{idx}, field_union);
        end
    end
else
    for idx = 1:numel(container)
        if isstruct(container(idx))
            container(idx) = ensure_field_set(container(idx), field_union);
        end
    end
end
end

