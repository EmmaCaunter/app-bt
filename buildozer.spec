[app]

# (str) Title of your application
title = Appix

# (str) Package name
package.name = appix

# (str) Package domain (needed for android/ios packaging)
package.domain = com.appix

# (str) Source code where the main.py live
# NOTE: I have this mounted as a shared folder in the Kivy Virtualbox VM, but this buildozer.spec is outside of it.
#source.dir = /media/sf_dev
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json,zip,ttf

# (list) Source files to exclude (let empty to not exclude anything)
#source.exclude_exts = spec

# (list) List of directory to exclude (let empty to not exclude anything)
#source.exclude_dirs = tests, bin

# (list) List of exclusions using pattern matching
#source.exclude_patterns = license,images/*/*.jpg

# (str) Application versioning (method 1)
version.regex = __version__ = ['"](.*)['"]
version.filename = %(source.dir)s/main.py

# (str) Application versioning (method 2)
# version = 1.0.0

# (list) Application requirements
# comma seperated e.g. requirements = sqlite3,kivy
requirements = kivy==1.10.0,pyjnius==1.1.0,plyer==1.3.0,numpy,audiostream,raven==5.9.2,openssl,requests

# (list) Garden requirements
#garden_requirements =

# (str) Presplash of the application
presplash.filename = %(source.dir)s/assets/appix-logo.jpg
#presplash.filename =/media/sf_Appix/App__v1__Build__/dev/assets/appix-logo.jpg


# (str) Icon of the application
icon.filename = %(source.dir)s/assets/appix-icon.png
#icon.filename =/media/sf_Appix/App__v1__Build__/dev/assets/appix-icon.png

# (str) Supported orientation (one of landscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 1


#
# Android specific
#

# (list) Permissions
android.permissions = INTERNET, BLUETOOTH, BLUETOOTH_ADMIN, FLASHLIGHT, CAMERA, VIBRATE, RECORD_AUDIO, ACCESS_COARSE_LOCATION, ACCESS_FINE_LOCATION

# (int) Android API to use
android.api = 23

# (int) Minimum API required (8 = Android 2.2 devices)
android.minapi = 19

# (int) Android SDK version to use
android.sdk = 24

# (str) Android NDK version to use
android.ndk = 10e

# (bool) Use --private data storage (True) or --dir public storage (False)
#android.private_storage = True

# (str) Android NDK directory (if empty, it will be automatically downloaded.)
#android.ndk_path = ../ndk

# (str) Android SDK directory (if empty, it will be automatically downloaded.)
#android.sdk_path = ../sdk

# (str) python-for-android git clone directory (if empty, it will be automatically cloned from github)
p4a.source_dir = ../python-for-android
#p4a.source_dir = ~/python-for-android


# (list) python-for-android whitelist
#android.p4a_whitelist =

# (str) Android entry point, default is ok for Kivy-based app
#android.entrypoint = org.renpy.android.PythonActivity

# (list) List of Java .jar files to add to the libs so that pyjnius can access
# their classes. Don't add jars that you do not need, since extra jars can slow
# down the build process. Allows wildcards matching, for example:
# OUYA-ODK/libs/*.jar
#android.add_jars = foo.jar,bar.jar,path/to/more/*.jar

# (list) List of Java files to add to the android project (can be java or a
# directory containing the files)
android.add_src = %(source.dir)s/java

# (str) python-for-android branch to use, if not master, useful to try
# not yet merged features.
#android.branch = master

# (str) OUYA Console category. Should be one of GAME or APP
# If you leave this blank, OUYA support will not be enabled
#android.ouya.category = GAME

# (str) Filename of OUYA Console icon. It must be a 732x412 png image.
#android.ouya.icon.filename = %(source.dir)s/data/ouya_icon.png

# (str) XML file to include as an intent filters in <activity> tag
#android.manifest.intent_filters =

# (list) Android additionnal libraries to copy into libs/armeabi
#android.add_libs_armeabi = libs/android/*.so
#android.add_libs_armeabi_v7a = libs/android-v7/*.so
#android.add_libs_x86 = libs/android-x86/*.so
#android.add_libs_mips = libs/android-mips/*.so

# (bool) Indicate whether the screen should stay on
# Don't forget to add the WAKE_LOCK permission if you set this to True
#android.wakelock = False

# (list) Android application meta-data to set (key=value format)
#android.meta_data =

# (list) Android library project to add (will be added in the
# project.properties automatically.)
#android.library_references =

#
# iOS specific
#

# (str) Name of the certificate to use for signing the debug version
# Get a list of available identities: buildozer ios list_identities
#ios.codesign.debug = "iPhone Developer: <lastname> <firstname> (<hexstring>)"

# (str) Name of the certificate to use for signing the release version
#ios.codesign.release = %(ios.codesign.debug)s


[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1


#    -----------------------------------------------------------------------------
#    List as sections
#
#    You can define all the "list" as [section:key].
#    Each line will be considered as a option to the list.
#    Let's take [app] / source.exclude_patterns.
#    Instead of doing:
#
#[app]
#source.exclude_patterns = license,data/audio/*.wav,data/images/original/*
#
#    This can be translated into:
#
#[app:source.exclude_patterns]
#license
#data/audio/*.wav
#data/images/original/*
#


#    -----------------------------------------------------------------------------
#    Profiles
#
#    You can extend section / key with a profile
#    For example, you want to deploy a demo version of your application without
#    HD content. You could first change the title to add "(demo)" in the name
#    and extend the excluded directories to remove the HD content.
#
#[app@demo]
#title = My Application (demo)
#
#[app:source.exclude_patterns@demo]
#images/hd/*
#
#    Then, invoke the command line with the "demo" profile:
#
#buildozer --profile demo android debug
