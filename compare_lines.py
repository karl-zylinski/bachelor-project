l1fh = open("l1.txt")
l1 = l1fh.readlines()
l1fh.close()

l2fh = open("l2.txt")
l2 = l2fh.readlines()
l2fh.close()

matches = 0
for l1item in l1:
    for l2item in l2:
        if l2item == l1item:
            matches = matches + 1
            break

print("%d/%d" % (matches, len(l1)))