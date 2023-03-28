import csv,json

# Read newmenu.csv and write to newmenu.json

with open("newmenu.csv","r") as file:
    reader = csv.DictReader(file)
    data = list(reader)
    print(data)
    f = json.dumps(data,indent=2)
    with open("newmenu.json","w") as file:
        file.write(f)