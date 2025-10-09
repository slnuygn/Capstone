function [clean_data] = reject_components(data, ICApplied, rejected_comps)
% REJECT_COMPONENTS Rejects components from data based on ICA results
%   [clean_data] = reject_components(data, ICApplied, rejected_comps)
%
% Inputs:
%   data - Cell array of raw data structures
%   ICApplied - Cell array of ICA results
%   rejected_comps - Cell array of components to reject
%
% Outputs:
%   clean_data - Cell array of cleaned data structures

clean_data = cell(size(data));

if nargin < 3 || isempty(rejected_comps)
    rejected_comps = cell(size(data));
end

if ~iscell(rejected_comps)
    rejected_comps = {rejected_comps};
end

if numel(rejected_comps) < numel(data)
    rejected_comps(end+1:numel(data)) = {[]}; %#ok<AGROW>
elseif numel(rejected_comps) > numel(data)
    warning('reject_components:SelectionLengthMismatch', ...
        'Received %d rejection entries for %d subjects. Truncating extras.', ...
        numel(rejected_comps), numel(data));
    rejected_comps = rejected_comps(1:numel(data));
end

for i = 1:length(data)
    if i > numel(rejected_comps) || isempty(rejected_comps{i})
        components_to_reject = [];
    else
        components_to_reject = normalize_components(rejected_comps{i});
    end
    
    if isempty(components_to_reject)
        clean_data{i} = data{i};
    else
        cfg = [];
        cfg.component = components_to_reject; % the components you want to remove
        clean_data{i} = ft_rejectcomponent(cfg, ICApplied{i}, data{i});
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