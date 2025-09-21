import scipy.io
import numpy as np

# Load the ICA data file
mat_data = scipy.io.loadmat('C:/Users/mamam/Desktop/data/data_ICA.mat')
print('All variables:', list(mat_data.keys()))

# Check data_ICApplied structure
if 'data_ICApplied' in mat_data:
    data = mat_data['data_ICApplied']
    print(f'data_ICApplied type: {type(data)}')
    print(f'data_ICApplied shape: {data.shape}')
    print(f'data_ICApplied dtype: {data.dtype}')
    
    if data.size > 0:
        print(f'First few elements: {data.flat[:10]}')
        
        # If it's a struct array, check its fields
        if data.dtype.names:
            print(f'Struct fields: {data.dtype.names}')
            for field in data.dtype.names:
                field_data = data[field][0,0]
                print(f'  {field}: shape={field_data.shape if hasattr(field_data, "shape") else "scalar"}, type={type(field_data)}')
        else:
            # Check if it contains references to other data
            if data.shape == (1, 2):
                for i in range(data.shape[1]):
                    elem = data[0, i]
                    print(f'Element [0,{i}]: shape={elem.shape if hasattr(elem, "shape") else "scalar"}, type={type(elem)}')
                    if hasattr(elem, 'dtype') and elem.dtype.names:
                        print(f'  Struct fields: {elem.dtype.names}')
                        for field in elem.dtype.names:
                            try:
                                field_data = elem[field][0,0] if elem[field].size > 0 else None
                                if field_data is not None:
                                    print(f'    {field}: shape={field_data.shape if hasattr(field_data, "shape") else "scalar"}')
                            except:
                                print(f'    {field}: could not access')
