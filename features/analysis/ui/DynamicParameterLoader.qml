import QtQuick 2.15
import QtQuick.Controls 2.15
import "../../preprocessing/ui"

Item {
    id: dynamicParameterLoader
    width: parent.width
    height: parameterComponentLoader.height

    property string parameterName: ""
    property var parameterConfig: ({})
    property bool editModeEnabled: false

    // MATLAB executor is available globally as matlabExecutor context property

    // Signal to notify when parameter value changes
    signal parameterChanged(string parameterName, var value)

    Loader {
        id: parameterComponentLoader
        width: parent.width / 2

        sourceComponent: {
            if (!parameterConfig || !parameterConfig.component_type) {
                return null;
            }

            switch (parameterConfig.component_type) {
                case "RangeSliderTemplate":
                    return rangeSliderComponent;
                case "DropdownTemplate":
                    return dropdownComponent;
                case "TriSliderTemplate":
                    return triSliderComponent;
                default:
                    return null;
            }
        }
    }

    Component {
        id: rangeSliderComponent

        RangeSliderTemplate {
            id: rangeSlider
            sliderId: parameterConfig.parameter_name || "dynamic_slider"
            label: parameterConfig.label || parameterName
            matlabProperty: parameterConfig.matlab_property || ""
            from: parameterConfig.from || 0
            to: parameterConfig.to || 1
            firstValue: parameterConfig.first_value || parameterConfig.from || 0
            secondValue: parameterConfig.second_value || parameterConfig.to || 1
            stepSize: parameterConfig.step_size || 0.1
            unit: parameterConfig.unit || ""
            backgroundColor: parameterConfig.background_color || "white"
            sliderState: editModeEnabled ? "edit" : "default"

                    onFirstValueChanged: {
                        if (initialized) {
                            dynamicParameterLoader.parameterChanged(parameterName, [firstValue, secondValue]);
                            // Auto-save to MATLAB
                            matlabExecutor.saveRangeSliderPropertyToMatlab(parameterConfig.matlab_property, firstValue, secondValue, parameterConfig.unit || "");
                        }
                    }

                    onSecondValueChanged: {
                        if (initialized) {
                            dynamicParameterLoader.parameterChanged(parameterName, [firstValue, secondValue]);
                            // Auto-save to MATLAB
                            matlabExecutor.saveRangeSliderPropertyToMatlab(parameterConfig.matlab_property, firstValue, secondValue, parameterConfig.unit || "");
                        }
                    }            property bool initialized: false
            Component.onCompleted: {
                initialized = true;
            }
        }
    }

    Component {
        id: dropdownComponent

        DropdownTemplate {
            id: dropdown
            label: parameterConfig.label || parameterName
            matlabProperty: parameterConfig.matlab_property || ""
            model: parameterConfig.model || []
            currentIndex: parameterConfig.current_index || 0
            hasAddFeature: parameterConfig.has_add_feature || false
            isMultiSelect: parameterConfig.is_multi_select || false
            maxSelections: parameterConfig.max_selections || -1
            allItems: parameterConfig.all_items || []
            selectedItems: parameterConfig.selected_items || []
            dropdownState: editModeEnabled ? "edit" : "default"

            onSelectionChanged: {
                if (isMultiSelect) {
                    dynamicParameterLoader.parameterChanged(parameterName, selectedItems);
                    // Auto-save to MATLAB
                    var needsCellFormat = parameterConfig.is_multi_select && (parameterConfig.max_selections !== 1);
                    matlabExecutor.saveDropdownPropertyToMatlab(parameterConfig.matlab_property, selectedItems, needsCellFormat);
                } else {
                    dynamicParameterLoader.parameterChanged(parameterName, model[currentIndex]);
                    // Auto-save to MATLAB
                    matlabExecutor.saveDropdownPropertyToMatlab(parameterConfig.matlab_property, [model[currentIndex]], false);
                }
            }

            onMultiSelectionChanged: {
                dynamicParameterLoader.parameterChanged(parameterName, selectedItems);
                // Auto-save to MATLAB
                var needsCellFormat = parameterConfig.is_multi_select && (parameterConfig.max_selections !== 1);
                matlabExecutor.saveDropdownPropertyToMatlab(parameterConfig.matlab_property, selectedItems, needsCellFormat);
            }
        }
    }

    Component {
        id: triSliderComponent

        TriSliderTemplate {
            id: triSlider
            sliderId: parameterConfig.parameter_name || "dynamic_tri_slider"
            label: parameterConfig.label || parameterName
            matlabProperty: parameterConfig.matlab_property || ""
            from: parameterConfig.from || 0
            to: parameterConfig.to || 1
            firstValue: parameterConfig.first_value || parameterConfig.from || 0
            secondValue: parameterConfig.second_value || (parameterConfig.from + parameterConfig.to) / 2 || 0.5
            thirdValue: parameterConfig.third_value || parameterConfig.to || 1
            stepSize: parameterConfig.step_size || 0.1
            unit: parameterConfig.unit || ""
            sliderState: editModeEnabled ? "edit" : "default"

            onRangeChanged: {
                dynamicParameterLoader.parameterChanged(parameterName, [firstValue, secondValue, thirdValue]);
                // Auto-save to MATLAB
                matlabExecutor.saveTriSliderPropertyToMatlab(parameterConfig.matlab_property, firstValue, secondValue, thirdValue, parameterConfig.step_size || 0.1, parameterConfig.unit || "");
            }
        }
    }

    // Function to get current parameter value
    function getCurrentValue() {
        if (parameterComponentLoader.item) {
            if (parameterConfig.component_type === "RangeSliderTemplate") {
                return [parameterComponentLoader.item.firstValue, parameterComponentLoader.item.secondValue];
            } else if (parameterConfig.component_type === "DropdownTemplate") {
                if (parameterComponentLoader.item.isMultiSelect) {
                    return parameterComponentLoader.item.selectedItems;
                } else {
                    return parameterComponentLoader.item.model[parameterComponentLoader.item.currentIndex];
                }
            }
        }
        return null;
    }

    // Function to set parameter value
    function setValue(value) {
        if (!parameterComponentLoader.item) return;

        if (parameterConfig.component_type === "RangeSliderTemplate" && Array.isArray(value) && value.length >= 2) {
            parameterComponentLoader.item.firstValue = value[0];
            parameterComponentLoader.item.secondValue = value[1];
        } else if (parameterConfig.component_type === "DropdownTemplate") {
            if (parameterComponentLoader.item.isMultiSelect && Array.isArray(value)) {
                parameterComponentLoader.item.selectedItems = value;
            } else if (typeof value === "string") {
                var index = parameterComponentLoader.item.model.indexOf(value);
                if (index !== -1) {
                    parameterComponentLoader.item.currentIndex = index;
                }
            }
        }
    }
}