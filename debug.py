with open('views/product_configurator_widget.py', 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Check what's around chk_primer
idx = content.find('self.chk_primer = QCheckBox')
if idx > 0:
    print("Around chk_primer:")
    print(repr(content[idx:idx+200]))
else:
    print("chk_primer not found")