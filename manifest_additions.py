pythonForAndroidLocation = "../python-for-android"


textAddToManifest = '''

        <service android:name="com.appix.bt.BluetoothLEService"
		android:exported="false"
		android:process=":python" />

	<service
	  android:name="com.appix.update.UpdateSchedulerService"
	  android:permission="android.permission.BIND_JOB_SERVICE"
	  android:exported="true"/>

	<receiver android:name="com.appix.update.UpdateBroadcastReceiver">
	    <intent-filter>
		<action android:name="com.appix.alarms.UPDATE" />
	    </intent-filter>
	</receiver>
'''

my_file_name = pythonForAndroidLocation + "/dist/appix/templates/AndroidManifest.tmpl.xml"


found_appl = False
found_insert_point = False
print "File located at: " +  my_file_name

write_lines = []
with open(my_file_name, 'r+') as manifest:
    print "Opening file..."
    for line in manifest:
        write_lines.append(line)
        if found_insert_point:
            continue
        elif "<application " in line:
            found_appl = True
        elif found_appl and ">" in line:
            write_lines.append(textAddToManifest)
            found_insert_point = True
	    print "Updating file..."
    manifest.seek(0)
    manifest.writelines(write_lines)
print "Manifest file updated successfully!"
            
