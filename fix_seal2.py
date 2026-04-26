import re

with open('views/product_configurator_widget.py', 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Add chk_seal after chk_primer
old = '''self.chk_primer = QCheckBox("грунт")

        self.chk_primer.setVisible(False)'''
new = '''self.chk_primer = QCheckBox("грунт")
        self.chk_seal = QCheckBox("Уплотнитель")

        self.chk_primer.setVisible(False)
        self.chk_seal.setVisible(False)'''

content = content.replace(old, new)

# Add to layout - find exact pattern
old2 = 'color_options_layout.addWidget(self.chk_primer)'
new2 = '''color_options_layout.addWidget(self.chk_primer)
        color_options_layout.addWidget(self.chk_seal)'''

content = content.replace(old2, new2)

# Add to toggle - find exact pattern 
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

with open('views/product_configurator_widget.py', 'w', encoding='utf-8-sig') as f:
    f.write(content)

print('Done')