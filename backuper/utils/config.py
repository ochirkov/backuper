import yaml
import jinja2
import re


class Config:

    _extra_vars_pattern = re.compile(r'(\S+)=(".*?"|\S+)')

    def __init__(self, args):
        self.args = args

    def _load_yaml(self, f):
        return yaml.load(f)

    def _parse_vars(self):
        return self._load_yaml(self.args.vars_file) if self.args.vars_file else {}

    def _parse_extra_vars(self):
        matches = self._extra_vars_pattern.findall(self.args.extra_vars)
        return {name: value for name, value in matches}

    def _get_jinja_template(self, r_template, args):
        t = jinja2.Template(r_template, undefined=jinja2.StrictUndefined)
        return t.render(args)

    def _merge_vars(self):
        return {**self._parse_vars(), **self._parse_extra_vars()}

    def parse_action(self):
        return self._load_yaml(
            self._get_jinja_template(self.args.action_file.read(), self._merge_vars()),
        )
