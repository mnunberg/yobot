all: main_auto.py chatwindow_auto.py \
	sendjoin_auto.py buddy_entry.py \
	notification.py resources_rc.py \
	smileys_rc.py logbrowser.py \
	logdlg.py status_dialog.py \
	triviaopts.py connection_properties.py \
	agent_connect_dlg.py _config_dialog.py \
	_account_settings.py

resources_rc.py: resources.qrc
	pyrcc4 $^ -o $@
smileys_rc.py: smileys.qrc
	pyrcc4 $^ -o $@

%.py: %.ui
	pyuic4 -x $^ -o $@
