def createNewUser(input):
	import csv
	with open('members.csv','a')as csvfile:
		writer = csv.writer(csvfile)
		writer.writerow([input])