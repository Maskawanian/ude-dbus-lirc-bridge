import pygtk
pygtk.require('2.0')
import gobject
gobject.threads_init ()
import gtk
gtk.gdk.threads_init()
import sys,os
import dbus
import dbus.service
import dbus.mainloop.glib
import pylirc
import select
import threading

dbusobj = None
quit = False
worker = None

class Example(dbus.service.Object):
	def __init__(self, bus, object_path):
		dbus.service.Object.__init__(self, bus, object_path)
	
	@dbus.service.signal(dbus_interface='org.ude.IR', signature='s')
	def IREvent(self, code):
		pass
	
	@dbus.service.method(dbus_interface='org.ude.IR')
	def Quit(self):
		worker.stop()
		worker.join()
		gtk.main_quit()
		pass

class IRWorker(threading.Thread):
	def __init__(self):
		super(IRWorker, self).__init__()
		self._stop = threading.Event()
	
	def stop(self):
		self._stop.set()
	
	def stopped(self):
		return self._stop.isSet()
	
	def run(self):
		try:
			lirchandle = pylirc.init("ude-dbus-lirc-bridge", "/usr/share/ude/dbus-lirc-bridge/lircrc", True)
			if lirchandle:
				while True:
					if self.stopped():
						break;
					try:
						timeout = select.select([lirchandle], [], [], 1) == ([], [], [])
					except Exception,e:
						print "IRWorker Exception",e
						continue
			
					if not timeout:
						s = pylirc.nextcode()
						if s:
							for code in s:
								if dbusobj:
									dbusobj.IREvent(code)
								#print "cmd",code
			pylirc.exit()
		except Exception,e:
			print "IRWorker Exception",e

if __name__ == "__main__":
	dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
	bus = dbus.SessionBus ()
	if bus.name_has_owner("org.ude.IR"):
		print "Instance already running."
		sys.exit()
	
	name = dbus.service.BusName("org.ude.IR", bus)
	dbusobj = Example(bus, '/org/ude/IR')
	
	worker = IRWorker()
	worker.start()
	
	gtk.main()







