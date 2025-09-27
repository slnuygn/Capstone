% Test script for the modified ICA rejection logic
% This script demonstrates the simple array logic implementation

fprintf('=== Testing ICA Rejection Logic ===\n');

% Simulate the scenario where we have multiple subjects
num_subjects = 3;

% Initialize the array (same as in browse_ICA.m)
rejected_ICs_array = cell(num_subjects, 1);
for j = 1:num_subjects
    rejected_ICs_array{j} = [];  % Initialize as empty array for each subject
end

fprintf('Initial array:\n');
for i = 1:num_subjects
    fprintf('Subject %d: [%s]\n', i, num2str(rejected_ICs_array{i}));
end

% Simulate rejecting components for different subjects
fprintf('\nSimulating rejections...\n');

% Subject 1: reject component 3
rejected_ICs_array{1} = [rejected_ICs_array{1}, 3];
fprintf('Subject 1: Rejected component 3 -> [%s]\n', num2str(rejected_ICs_array{1}));

% Subject 1: reject another component 7
rejected_ICs_array{1} = [rejected_ICs_array{1}, 7];
fprintf('Subject 1: Rejected component 7 -> [%s]\n', num2str(rejected_ICs_array{1}));

% Subject 2: reject component 2
rejected_ICs_array{2} = [rejected_ICs_array{2}, 2];
fprintf('Subject 2: Rejected component 2 -> [%s]\n', num2str(rejected_ICs_array{2}));

% Subject 3: no rejections (stays empty)
fprintf('Subject 3: No rejections -> [%s]\n', num2str(rejected_ICs_array{3}));

fprintf('\nFinal array state:\n');
for i = 1:num_subjects
    if isempty(rejected_ICs_array{i})
        fprintf('Subject %d: No components rejected\n', i);
    else
        fprintf('Subject %d: Rejected components [%s]\n', i, num2str(rejected_ICs_array{i}));
    end
end

% Test script saving functionality
fprintf('\nTesting script saving...\n');
timestamp = datestr(now, 'yyyy-mm-dd_HH-MM-SS');
script_filename = sprintf('test_rejected_ICs_%s.m', timestamp);

fid = fopen(script_filename, 'w');
if fid ~= -1
    fprintf(fid, '%% Test Rejected ICA Components Results\n');
    fprintf(fid, '%% Generated on: %s\n', datestr(now));
    fprintf(fid, '%% Total subjects: %d\n\n', length(rejected_ICs_array));
    
    fprintf(fid, 'rejected_ICs_array = {\n');
    for i = 1:length(rejected_ICs_array)
        if isempty(rejected_ICs_array{i})
            fprintf(fid, '    []; %% Subject %d: No rejected components\n', i);
        else
            fprintf(fid, '    [%s]; %% Subject %d: Rejected components\n', num2str(rejected_ICs_array{i}), i);
        end
    end
    fprintf(fid, '};\n');
    
    fclose(fid);
    fprintf('Test results saved to: %s\n', script_filename);
else
    fprintf('Could not create test file\n');
end

fprintf('\n=== Test Complete ===\n');