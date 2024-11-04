# This uses the mkdocs-macros-plugin to include files in markdown files
# See: https://mkdocs-macros-plugin.readthedocs.io/en/latest/
# Usage: {% include_file "path/to/file" %}

# We added this so we can include the google translate code in the markdown files
# This is useful to avoid having to copy and paste the code in every markdown file

# To get this to work, we need to install the mkdocs-macros-plugin, and we need
# to add the following to the mkdocs.yml file:
# plugins:
#   - macros

# You also need to install the mkdocs-macros-plugin
# pip install mkdocs-macros-plugin

# We added this to requirements.txt

# To include a file, use the following syntax:
# {{ include_file('docs/translate.html') }}

from pathlib import Path

def define_env(env):
    @env.macro
    def include_file(filepath):
        with open(Path(filepath), 'r') as f:
            return f.read()