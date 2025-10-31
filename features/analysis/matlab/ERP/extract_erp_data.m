function output = extract_erp_data(ERP_struct, condition_name)
% extract_erp_data Extracts avg data for a given condition (e.g., 'target', 'standard', 'novelty')
% 
% Usage:
%   output = extract_erp_data(ERP_struct, 'target')
%
% Inputs:
%   ERP_struct - array of structs (e.g., ERP_old or ERP_young)
%   condition_name - string: 'target', 'standard', or 'novelty'
%
% Output:
%   output - cell array containing avg' data from the specified condition

    output = cell(length(ERP_struct), 1);
    
    for i = 1:length(ERP_struct)
        output{i} = ERP_struct(i).(condition_name).avg';
    end
end
