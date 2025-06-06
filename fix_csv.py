import csv

def fix_csv(input_file, output_file):
    with open(input_file, 'r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    for line in lines:
        # Split the line by multiple spaces
        parts = [p for p in line.split('  ') if p.strip()]
        # Join with commas
        fixed_line = ','.join(parts)
        fixed_lines.append(fixed_line)
    
    with open(output_file, 'w') as f:
        f.writelines(fixed_lines)

if __name__ == '__main__':
    fix_csv('products.csv', 'products_fixed.csv') 