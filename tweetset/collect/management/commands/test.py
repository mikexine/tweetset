key = "ger, ita, gerita"

key_list = key.replace(" ", "").split(",")
print key_list
time_dict = {}
for k in key_list:
	time_dict[k] = []
print time_dict


for k in time_dict:
	print k
	if k == "ita":
		print time_dict[k]