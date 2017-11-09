import sublime
import sublime_plugin

import os
from threading import Timer
from tempfile import mkstemp
from subprocess import Popen, PIPE
import re

def _get_wincc(key):
	proj_data = sublime.active_window().project_data()
	if 'wincc' in proj_data.keys():
		wincc_data = proj_data['wincc']
		if key in wincc_data.keys():
			return wincc_data[key]
	return None

class AllTestsCommand(sublime_plugin.WindowCommand):
	def run(self):
		cspa_main_path = _get_wincc('cspa_main_path')
		wincc_ver = _get_wincc('wincc_ver')
		test_bat = os.path.join(cspa_main_path, 'test.bat')

		if cspa_main_path == None or wincc_ver == None:
			sublime.error_message('cspa_main_path or wincc_ver not set in project file')
			return

		if not os.path.exists(test_bat):
			sublime.error_message('%s not found'%(test_bat))
			return

		close = ""
		if self.window.settings().has('close_checked') and self.window.settings().get('close_checked'):
			close = 'close'

		sublime.active_window().run_command('exec', {'cmd':'%s %s "all.tests,%s"'%(test_bat,wincc_ver, close)});

	def is_enabled(self):
		return _get_wincc('wincc_oa_path') != None

class ThisTestCommand(sublime_plugin.WindowCommand):
	def run(self):
		fn = os.path.splitext(os.path.basename(self.window.active_view().file_name()))[0]
		cspa_main_path = _get_wincc('cspa_main_path')
		wincc_ver = _get_wincc('wincc_ver')
		test_bat = os.path.join(cspa_main_path, 'test.bat')

		if cspa_main_path == None or wincc_ver == None:
			sublime.error_message('cspa_main_path or wincc_ver not set in project file')
			return

		test_path = self._get_test_script_for_module(self.window.active_view().file_name())

		if not os.path.exists(test_path):
			sublime.error_message('no test scipt for module %s'%(fn,))
			return

		test_bat = os.path.join(cspa_main_path, 'test.bat')

		if not os.path.exists(test_bat):
			sublime.error_message('%s not found'%(test_bat))
			return

		close = ""
		if self.window.settings().has('close_checked') and self.window.settings().get('close_checked'):
			close = 'close'

		for v in self.window.views():
			v.run_command('save');

		self.window.run_command('exec', {'cmd':'%s %s "%s,%s"'%(test_bat,wincc_ver, fn,close)});

	def description(self):
		fn = "'none'"
		if self.is_enabled():
			fn = os.path.splitext(os.path.basename(self.window.active_view().file_name()))[0]
		
		return 'Test %s'%(fn)
		
	def is_enabled(self):
		return self.window.active_view().settings().get('syntax') == 'Packages/WinCC/wincc.sublime-syntax'

	def _get_test_script_for_module(self, module_path):
		test_path = module_path.replace('modules', 'tests')
		return test_path

class CheckControlSyntaxCommand(sublime_plugin.WindowCommand):
	def run(self):
		script_path = os.path.join(_get_wincc('cspa_main_path'), 'scripts')
		wincc_oa_path = _get_wincc('wincc_oa_path')
		wccoactrl = os.path.join(wincc_oa_path, 'bin', 'wccoactrl.exe')
		file_sub_path = os.path.relpath(self.window.active_view().file_name(), script_path)
		self.window.active_view().run_command('save')
		proc = Popen("%s  -syntax -log -file -log +stderr -currentproj %s"%(wccoactrl, file_sub_path), stderr = PIPE, stdout = PIPE, shell = True)
		(so, se) = proc.communicate()

		if(proc.returncode != 0):
			result = re.search(r'Syntax error, .*ctl Line: (\d*) Column: (\d*),', str(se))
			if(result != None):
				row = int(result.group(1))
				col = int(result.group(2))
				text_pos = self.window.active_view().text_point(row, col)
				self.window.run_command('show_overlay', {'overlay':'goto', 'text':':%i:%i'%(row, col)})
				self.window.run_command('hide_overlay')

	def description(self):
		fn = "'none'"
		if self.is_enabled():
			fn = os.path.splitext(os.path.basename(self.window.active_view().file_name()))[0]
			
		return 'Syntax check %s'%(fn)

	def is_enabled(self):
		return self.window.active_view().settings().get('syntax') == 'Packages/WinCC/wincc.sublime-syntax'


class SetCloseCheckedCommand(sublime_plugin.WindowCommand):
	def run(self):
		state = self.window.settings().get('close_checked')
		self.window.settings().set('close_checked', not state)
		
	def is_enabled(self):
		return self.window.active_view().settings().get('syntax') == 'Packages/WinCC/wincc.sublime-syntax'

	def is_checked(self):
		return self.window.settings().has('close_checked') and self.window.settings().get('close_checked')

class EventListener(sublime_plugin.ViewEventListener):
	@classmethod
	def is_applicable(self, settings):
		return settings.get('syntax') == 'Packages/WinCC/wincc.sublime-syntax';

	@classmethod
	def applies_to_primary_view_only(self):
		return True

	def __init__(self, view):
		#self.timer = Timer(1, self._syntax_check);
		self.view = view
		self.wccoactrl = 'C:\\Siemens\\Automation\\WinCC_OA\\3.14\\bin\\WCCOActrl.exe'

	#def on_modified(self):
	#	if self.timer.is_alive():
	#		self.timer.cancel();
#
#		self.timer = Timer(1, self._syntax_check);
#		self.timer.start();

	def on_load(self):
		self._syntax_check()

	def _syntax_check(self):
		fname = "test.ctl"
		
		print(output_str)
		os.remove(fname)

	def _create_temp_file(self):
		(fhandle, fname) = mkstemp(text=True);
		fd = os.fdopen(fhandle, 'w')
		buff = self.view.substr(sublime.Region(0, self.view.size()))
		fd.write(buff)
		fd.close()
		return fname

