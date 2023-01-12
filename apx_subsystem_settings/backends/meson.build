pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
backendsdir = join_paths(pkgdatadir, 'apx_subsystem_settings/backends')

sources = [
  '__init__.py',
  'apx.py',
  'exceptions.py',
]

install_data(sources, install_dir: backendsdir)
