with open('views/product_configurator_widget.py', 'r', encoding='utf-8-sig') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if 'chk_primer = QCheckBox' in line:
            print(f'Line {i+1}')
            print(f'Line{i+2}: {lines[i+1]}')
            print(f'Line{i+3}: {lines[i+2]}')
            print(f'Line{i+4}: {lines[i+3]}')
            break