import sys
import os
import shutil
import datetime

print("q: quit, y: yes, n: no, r: yes recursively for all subdirectories/files, d: yes in this directory")

META_SENSITIVE = False
NAME_SENSITIVE = True
TIME_SENSITIVE = False
TIME_MARGIN = 2 # FAT doesn't support the same time precision

if META_SENSITIVE:
	print("Copying meta data")
	COPY = shutil.copy2
else:
	print("Not copying meta data")
	def COPY(src, dst):
		try:
			shutil.copy(src, dst)
		except OSError as E:
			print(E)
			print("(This might not actually be a problem... Might wanna go check though)")

if NAME_SENSITIVE:
	print("Removing toxic characters")
	# "/" is also forbidden, but it's forbidden in UNIX as well, and is used as a path seperator
	TOXIC_CHARS = {"\"", "*", ":", "<", ">", "?", "\\", "|"}

	# To remove the name detoxing, just uncomment the "return name" line and comment out the previous "return" line
	def detox(name):
		return "".join(("_" if x in TOXIC_CHARS else x) for x in name)
else:
	print("Not removing toxic characters")
	def detox(name):
		return name

if TIME_SENSITIVE:
	print(f"Looking at timestamps ({TIME_MARGIN}ms margins)")
else:
	print("Not looking at timestamps")

def decide(prompt, default=None, choices=["y","n"]):
	if default:
		for i in range(len(choices)):
			if choices[i] == default:
				choices[i] = choices[i].upper()
				prompt += " (" + "/".join(choices) + ") "
				choices[i] = choices[i].lower()
				break
	else:
		prompt += " (" + "/".join(choices) + ") "

	choice = None
	while choice == None:
		choice = input(prompt)
		if len(choice) == 0:
			choice = default
		else:
			choice = choice[0].lower()
			if choice == "q":
				abort()
			if not choice in choices:
				choice = None
	return choice

if len(sys.argv) != 3:
	print("Needs two arguments: source directory and destination directory")
	quit()

SOURCE = sys.argv[1]
DEST = sys.argv[2]

# for things that were ignored:
EXTRA = []
MISSING = []
OUTDATED = []
INDATED = []
PERMISSION = []

def syncDirectory(path):
	print(f"Syncing: \"{path}\"")
	absSourcePath = os.path.join(SOURCE, path)
	absDestPath = os.path.join(DEST, path)

	sourceSubdirs = set()
	sourceFiles = set()
	detoxMap = {}
	try:
		for obj in os.scandir(absSourcePath):
			if obj.is_file():
				newName = detox(os.path.relpath(obj.path, SOURCE))
				sourceFiles.add(newName)
			elif obj.is_dir():
				newName = detox(os.path.relpath(obj.path, SOURCE))
				sourceSubdirs.add(newName)
			else:
				print(f"Didn't recognize: \"{obj.path}\"")
			detoxMap[newName] = obj.path
	except PermissionError as E:
		print(f"Couldn't access directory in source: \"{absSourcePath}\"")
		input("Ignoring it (it will be in the final census).")
		PERMISSION.append(absSourcePath)
		return

	destSubdirs = set()
	destFiles = set()
	try:
		for obj in os.scandir(absDestPath):
			relPath = os.path.relpath(obj.path, DEST)
			if obj.is_dir():
				destSubdirs.add(relPath)
			elif obj.is_file():
				destFiles.add(relPath)
			else:
				print(f"Did't recognize: \"{obj.path}\"")
	except PermissionError as E:
		print(f"Couldn't access directory in destination: \"{absDestPath}\"")
		print("Ignoring it (it will be in the final census).")
		PERMISSION.append(absDestPath)
		return

	toSearch = sourceSubdirs & destSubdirs

	# extra files
	goAhead = False
	for file in destFiles-sourceFiles:
		absFile = os.path.join(DEST, file)
		if goAhead:
			print(f"Deleting: \"{file}\"")
			os.remove(absFile)
			continue
		print(f"Extra file found in destination: \"{file}\"")
		decision = decide("Delete it?", choices=["y", "n", "d"])
		if decision == "y":
			os.remove(absFile)
			print("Deleted")
		elif decision == "d":
			goAhead = True
			print(f"Deleting: \"{file}\"")
			os.remove(absFile)
		else:
			EXTRA.append(file)

	# missing
	goAhead = False
	for file in sourceFiles-destFiles:
		absSourceFile = detoxMap[file]
		absDestFile = os.path.join(DEST, file)
		if goAhead:
			print(f"Adding: \"{file}\"")
			COPY(absSourceFile, absDestFile)
			continue
		print(f"Missing file not found in destination: \"{file}\"")
		decision = decide("Add it?", choices=["y", "n", "d"])
		if decision == "y":
			COPY(absSourceFile, absDestFile)
			print("Added")
		elif decision == "d":
			goAhead = True
			print(f"Adding: \"{file}\"")
			COPY(absSourceFile, absDestFile)
		else:
			MISSING.append(file)

	# timing
	if TIME_SENSITIVE:
		outdatedGoAhead = False
		indatedGoAhead = False
		for file in sourceFiles&destFiles:
			absSourceFile = detoxMap[file]
			absDestFile = os.path.join(DEST, file)
			sourceTime = os.stat(absSourceFile).st_mtime
			destTime = os.stat(absDestFile).st_mtime
			if abs(sourceTime-destTime) > TIME_MARGIN:
				prettySourceTime = datetime.datetime.fromtimestamp(sourceTime).strftime('%Y-%m-%d %H:%M:%S')
				prettyDestTime = datetime.datetime.fromtimestamp(destTime).strftime('%Y-%m-%d %H:%M:%S')

				if sourceTime > destTime:
					if outdatedGoAhead:
						print(f"Updating: \"{file}\"")
						COPY(absSourceFile, absDestFile)
						continue
					print(f"Outdated file found in destination (source: {prettySourceTime}, destination: {prettyDestTime}): \"{file}\"")
					decision = decide("Update it?", choices=["y", "n", "d"])
					if decision == "y":
						COPY(absSourceFile, absDestFile)
						print("Updated")
					elif decision == "d":
						outdatedGoAhead = True
						print(f"Updating: \"{file}\"")
						COPY(absSourceFile, absDestFile)
					else:
						OUTDATED.append(file)
				elif sourceTime < destTime:
					if indatedGoAhead:
						print(f"Downdating: \"{file}\"")
						COPY(absSourceFile, absDestFile)
						continue
					print(f"Indated file found in destination (source: {prettySourceTime}, destination: {prettyDestTime}): \"{file}\"")
					decision = decide("Downdate it anyway?", choices=["y", "n", "d"])
					if decision == "y":
						COPY(absSourceFile, absDestFile)
						print("Downdated")
					elif decision == "d":
						indatedGoAhead = True
						print(f"Downdating: \"{file}\"")
						COPY(absSourceFile, absDestFile)
					else:
						INDATED.append(file)

	goAhead = False
	for subdir in destSubdirs-sourceSubdirs:
		absSubdir = os.path.join(DEST, subdir)
		if goAhead:
			print(f"Deleting: \"{subdir}\"")
			shutil.rmtree(absSubdir)
			continue
		print(f"Extra subdirectory found in destination: \"{subdir}\"")
		decision = decide("Delete it (and all subdirectories/files)?", choices=["y", "n", "d"])
		if decision == "y":
			shutil.rmtree(absSubdir)
			print("Deleted")
		elif decision == "d":
			goAhead = True
			print(f"Deleting: \"{subdir}\"")
			shutil.rmtree(absSubdir)
		else:
			EXTRA.append(subdir)

	for subdir in sourceSubdirs-destSubdirs:
		absSourceSubdir = detoxMap[subdir]
		absDestSubdir = os.path.join(DEST, subdir)
		print(f"Missing subdirectory not found in destination: \"{subdir}\"")
		decision = decide("Add it?", choices=["y", "n", "r"])
		if decision == "y":
			os.mkdir(absDestSubdir)
			toSearch.add(subdir)
			print("Added")
		elif decision == "r":
			shutil.copytree(absSourceSubdir, absDestSubdir, copy_function=COPY)
			print("Entire tree copied")
		else:
			MISSING.append(subdir)

	for subdir in toSearch:
		syncDirectory(subdir)

def abort():
	print("Aborting!")
	if len(MISSING)+len(EXTRA)+len(OUTDATED)+len(INDATED)+len(PERMISSION):
		if decide(f"Logs available: {len(MISSING)} missing, {len(EXTRA)} extra, {len(OUTDATED)} outdated, and {len(INDATED)} indated. Also, {len(PERMISSION)} permission errors were encountered. View them?") == "y":
			print("\nMISSING:")
			for obj in MISSING:
				print(obj)
			print("\nEXTRA:")
			for obj in EXTRA:
				print(obj)
			print("\nOUTDATED:")
			for obj in OUTDATED:
				print(obj)
			print("\nINDATED:")
			for obj in INDATED:
				print(obj)
			print("\nPERMISSION:")
			for obj in PERMISSION:
				print(obj)
	quit()

syncDirectory("")
if len(MISSING)+len(EXTRA)+len(OUTDATED)+len(INDATED)+len(PERMISSION):
	if decide(f"Destination (almost) synced! {len(MISSING)} missing, {len(EXTRA)} extra, {len(OUTDATED)} outdated, and {len(INDATED)} indated left. Also, {len(PERMISSION)} permission errors were encountered. View them?") == "y":
		print("\nMISSING:")
		for obj in MISSING:
			print(obj)
		print("\nEXTRA:")
		for obj in EXTRA:
			print(obj)
		print("\nOUTDATED:")
		for obj in OUTDATED:
			print(obj)
		print("\nINDATED:")
		for obj in INDATED:
			print(obj)
		print("\nPERMISSION:")
		for obj in PERMISSION:
			print(obj)
else:
	print("Destination synced!")
