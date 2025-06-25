from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path


_ENV = Environment(
  loader=FileSystemLoader(f'{Path(__file__).parent}/templates/'),
  autoescape=select_autoescape()
)


def render_template(template_name: str, **kwargs) -> str:
  template = _ENV.get_template(template_name)
  return template.render(**kwargs)
