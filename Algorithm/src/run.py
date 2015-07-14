import os, sys
from process import *

class ConvertToMIDI(object):
	def __init__(self, InputFile):
		fin = open(InputFile, 'r')
		self.FileList = [line.strip('\n') for line in fin.readlines()]
		fin.close()

	def getMIDI(self):
		if not os.path.exists('MIDI'):
			os.system('mkdir MIDI')

		FileCnt = 0
		for perFile in self.FileList:
			if not os.path.exists(perFile):
				print '*******Error: ' + perFile + ' not exists.*******\n'
				return
			
			FileCnt += 1
			portion = os.path.split(perFile)
			name = os.path.splitext(portion[1])[0]
			cmd = 'bin/waon -i ' + perFile + ' -o ' + 'MIDI' + os.sep + name + '.mid -w 3 -n 4096 -s 2048'
			print '******Convert ' + str(FileCnt) + ' song.*******'
			os.system(cmd)
		print '******Conversion work done.*******'

class ExtractMIDIFeature(object):
	def __init__(self, InputFile):
		portion = os.path.split(InputFile)
		name = os.path.splitext(portion[1])[0]
		midiFileList = 'index' + os.sep + name + 'MIDI.list'

		if os.path.exists(midiFileList):
			self.midiFileList = midiFileList
			return

		fin = open(InputFile, 'r')
		fout = open(midiFileList, 'w')
		for line in fin.readlines():
			newLine = 'MIDI' + os.sep + line.split('/')[1].split('.')[0] + '.mid\n'
			fout.write(newLine)
		fout.close()
		fin.close()

		self.midiFileList = midiFileList
	
	def extractMIDIFeature(self):
		cmd = 'java -jar bin/mySymbolic.jar ' + self.midiFileList
		os.system(cmd)

		self.getMIDIFeature('scrach/value', 'MIDIFeature')

	def getPerMIDIFile(self, filename, newDir):
		lines = getlines(filename)
		i = 0
		while i < len(lines):
			line = lines[i].strip('\t\r\n')
			if "<data_set_id>" in line:
				fname = line.split('/')[-2].split('.')[0] + '.fea'
				i += 1
				data = []
				while i < len(lines):
					line = lines[i].strip('\t\r\n')
					if "<data_set_id>" in line:
						break
					if "<v>" in line:
						v_string = line[3:len(line)-4]
						data.append(v_string)
					i += 1
				save_file([['\t'.join(data) + '\n']], newDir + os.sep + fname)
			else:
				i += 1

	def getMIDIFeature(self, preDir, newDir):
		if not os.path.exists(newDir):
			os.system('mkdir MIDIFeature')
		fileList = os.listdir(preDir)
		for filename in fileList:
			self.getPerMIDIFile(preDir + os.sep + filename, newDir)

class ExtractAudioFeature(object):

	def __init__(self, fileList):
		self.fileList = fileList
		self.featureDir = 'audioFeature'
		
		if not os.path.exists(self.featureDir):
			os.system('mkdir audioFeature')

	def extractFeature(self):
		fin = open(self.fileList, "r")
		lines = fin.readlines()
		ext = Extractor(midLevel=False, highLevel=False, rhythm=False, tuning=False, dynamics=False, tonalFrameSize=2048, tonalHopSize=1024)

		cnt = 0
		for line in lines:
			cnt += 1
			print cnt

			fdire, fname = line.strip('\r\n').split('/')
			prefix = fname.split('.')[0]
		
			opath = self.featureDir + os.sep + prefix + '.fea'
			if os.path.exists(opath):
				continue
		
			audio = MonoLoader(filename=(fdire + os.sep + fname))()
			#pool = PoolAggregator()(ext(audio))
			pool = PoolAggregator(defaultStats=['mean'])(ext(audio))
			feature_list = pool.descriptorNames()
			feature = []
			for feature_name in feature_list:
				if type(pool[feature_name]) is float:
					feature.append(pool[feature_name])
				else:
					feature.extend(pool[feature_name])
			print 'feature len %d' %len(feature)
			save_file([['\t'.join(str(i) for i in feature)+'\n']], opath)

class InputAndOutput(object):

	def loadX(self, fileList, featureDir):
		X = []
		with open(fileList, 'r') as f:
			for line in f:
				name = line.strip('\r\n').split('/')[-1].split('.')[0]
				opath = featureDir + os.sep + name + '.fea'
				if os.path.exists(opath):
					line = getlines(opath)[0].strip('\r\n').split('\t')
					X.append([float(i) for i in line])
		return np.array(X)

	def loady(self, fileList):
		y = []
		with open(fileList, 'r') as f:
			for line in f:
				y.append(line.strip('\r\n'))
		return np.array(y)
	
	def writeBack(self, testList, predict_y, outList):
		fin = open(testList, 'r')
		lines = fin.readlines()
		fin.close()

		fout = open(outList, 'w')		
		for i in range(len(lines)):
			line = lines[i].strip('\r\n') + '\t' + predict_y[i] + '\n'
			fout.write(line)
		fout.close()
	

class RunSystem(object):

	def __init__(self, trainList, testList, outList):
		self.testList = testList
		self.outList = outList
		
		fDir = trainList.split('/')[0]
		self.trainList = fDir + os.sep + 'train.list'
		self.labelList = fDir + os.sep + 'label.list'
		
		if not os.path.exists(self.trainList):
			fin = open(trainList, 'r')
			lines = fin.readlines()
			fin.close()

			fout1 = open(self.trainList, 'w')
			fout2 = open(self.labelList, 'w')
			for line in lines:
				items = line.strip('\r\n').split('\t')
				fout1.write(items[0] + '\n')
				fout2.write(items[1] + '\n')
			fout1.close()
			fout2.close()

			self.mergeList = fDir + os.sep + 'merge.list'
		
			fout = open(self.mergeList, 'w')
			with open(self.trainList, 'r') as f:
				for line in f:
					fout.write(line)
			with open(self.testList, 'r') as f:
				for line in f:
					fout.write(line)
			fout.close()			

	def extractFeature(self):
		print "Convert wav to MIDI feature....."
		ctm = ConvertToMIDI(self.mergeList)
		ctm.getMIDI()
		
		print "Extracting MIDI Feature......"
		emf = ExtractMIDIFeature(self.mergeList)
		emf.extractMIDIFeature()

		print "Extracting Audio Feature......"
		ext = ExtractAudioFeature(self.mergeList)
		ext.extractFeature()

		print "Extracted All Features for acquired data, done!"

	def trainAndClassify(self):
		print "Start to load data"
		io = InputAndOutput()		
	
		Train_X1 = io.loadX(self.trainList, 'audioFeature')
		Train_X2 = io.loadX(self.trainList, 'MIDIFeature')
		Train_X = np.hstack((Train_X1, Train_X2))
		Train_X = normalize(X=Train_X, norm='l2', axis=0)

		Test_X1 = io.loadX(self.testList, 'audioFeature')
		Test_X2 = io.loadX(self.testList, 'MIDIFeature')
		Test_X = np.hstack((Test_X1, Test_X2))
		Test_X = normalize(X=Test_X, norm='l2', axis=0)

		Train_y = io.loady(self.labelList)
		print "Start to Train Model"

		#slt = sklearn.feature_selection.SelectKBest(sklearn.feature_selection.f_classif)
		#Train_X = slt.fit_transform(Train_X, Train_y)
		#Test_X = slt.transform(Test_X)
		clf = RandomForestClassifier()
		clf.fit_transform(Train_X, Train_y)
		predict_y = clf.predict(Test_X)

		io.writeBack(self.testList, predict_y, self.outList)
		print "Prediction Done. Please check outfile"
		

if __name__ == "__main__":
	if sys.argv[1] == '-ext':
		cmd = RunSystem(sys.argv[2], sys.argv[3], sys.argv[4])
		cmd.extractFeature()
	if sys.argv[1] == '-clf':
		cmd = RunSystem(sys.argv[2], sys.argv[3], sys.argv[4])
		cmd.trainAndClassify()
	
	
