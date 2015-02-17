#input format should be ['usrname']
def registedUser(input):
	import csv
	import string
	with open('members.csv','rb')as csvfile:
		reader = csv.reader(csvfile)
		for row in reader:
			if row == input:
				return True	
		return False
