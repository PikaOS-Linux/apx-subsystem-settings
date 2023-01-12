pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'apx_subsystem_settings')
gnome = import('gnome')

gnome.compile_resources('apx-subsystem-settings',
  'apx-subsystem-settings.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'apx-subsystem-settings.in',
  output: 'apx-subsystem-settings',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

subdir('backends')

apx_subsystem_settings_sources = [
  '__init__.py',
  'main.py',
  'window.py',
  'program.py',
  'run_async.py',
  'container.py',
  'dialog_installation.py',
]

install_data(apx_subsystem_settings_sources, install_dir: moduledir)
