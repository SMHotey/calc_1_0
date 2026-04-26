import re

with open('views/product_configurator_widget.py', 'rb') as f:
    raw = f.read()

# Detect encoding
if raw.startswith(b'\xff\xfe'):
    # UTF-16 LE
    content = raw.decode('utf-16')
elif raw.startswith(b'\xfe\xff'):
    # UTF-16 BE
    content = raw.decode('utf-16')
elif raw.startswith(b'\xef\xbb\xbf'):
    # UTF-8 with BOM
    content = raw[3:].decode('utf-8')
else:
    # Try UTF-8
    content = raw.decode('utf-8')

# Add chk_seal after chk_primer
old = 'self.chk_primer = QCheckBox("грунт")\n        self.chk_primer.setVisible(False)'
new = '''self.chk_primer = QCheckBox("грунт")
        self.chk_seal = QCheckBox("Уплотнитель")
        self.chk_primer.setVisible(False)
        self.chk_seal.setVisible(False)'''

content = content.replace(old, new)

# Add to layout
old2 = 'color_options_layout.addWidget(self.chk_primer)'
new2 = '''color_options_layout.addWidget(self.chk_primer)
        color_options_layout.addWidget(self.chk_seal)'''

content = content.replace(old2, new2)

# Add to toggle
old3 = 'self.chk_primer.setVisible(expanded)'
new3 = '''self.chk_primer.setVisible(expanded)
        self.chk_seal.setVisible(expanded)'''

content = content.replace(old3, new3)

# Add to color_options dict
old4 = '"primer": self.chk_primer.isChecked()\n              },\n              "extra_options"'
new4 = '''"primer": self.chk_primer.isChecked(),
                  "seal": self.chk_seal.isChecked()
              },
              "extra_options"'''

content = content.replace(old4, new4)

# Write back as UTF-8 with BOM
with open('views/product_configurator_widget.py', 'w', encoding='utf-8-sig') as f:
    f.write(content)

print('Done')