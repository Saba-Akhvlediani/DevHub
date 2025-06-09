from django import template

register = template.Library()

@register.filter
def index(sequence, position):
    """Get item from sequence by index"""
    try:
        return sequence[position]
    except (IndexError, TypeError):
        return None

@register.filter
def get_spec(product, spec_name):
    """Get product specification by name"""
    try:
        # Map spec names to model fields
        spec_map = {
            'Power': 'power',
            'Voltage': 'voltage',
            'Frequency': 'frequency',
            'Temperature Settings': 'temperature_settings',
            'Air Flow Settings': 'air_flow_settings',
            'Cable Length': 'cable_length',
            'Weight': 'weight',
            'Material': 'material',
            'Noise Level': 'noise_level',
            'Motor Type': 'motor_type',
            'Heating Element Type': 'heating_element_type'
        }
        
        # Get the field name from the map
        field_name = spec_map.get(spec_name)
        if field_name:
            return getattr(product, field_name, '-')
            
        # Check custom specifications
        if hasattr(product, 'specifications'):
            spec = product.specifications.filter(name=spec_name).first()
            if spec:
                return spec.value
                
        return '-'
    except Exception:
        return '-' 