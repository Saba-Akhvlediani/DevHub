from django import template

register = template.Library()

@register.filter
def get_spec(product, spec_name):
    """Get product specification by name"""
    # Check built-in specs first
    built_in_specs = {
        'Power': product.power,
        'Voltage': product.voltage,
        'Frequency': product.frequency,
        'Temperature Settings': product.temperature_settings,
        'Air Flow Settings': product.air_flow_settings,
        'Cable Length': product.cable_length,
        'Weight': product.weight,
        'Material': product.material,
        'Noise Level': product.noise_level,
        'Motor Type': product.motor_type,
        'Heating Element Type': product.heating_element_type,
    }
    
    if spec_name in built_in_specs:
        return built_in_specs[spec_name]
    
    # Check custom specs
    try:
        spec = product.specifications.get(name=spec_name)
        return spec.value
    except:
        return None 