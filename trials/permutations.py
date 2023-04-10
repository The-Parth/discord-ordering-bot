# Accept a number/string
no = input("Enter a number/string: ").strip()

def elements(n) -> list:
    # Returns a list of elements of n
    digits = [] # List to store individual elements
    n = str(n)
    for i in n:
        digits.append(i)
    return digits


def permute(n:int) -> list:
    # Returns a list of all permutations of the digits of a number n
    digs = elements(n) # List of digits of n
    permutations = [] # List to store permutations
    if len(digs) == 1: 
        # If n is a single digit number, return it as it is in a list
        # This is done so that we can determine if the last digit of a number is obtained
        return digs
    for i in digs:
        new_digs = digs.copy()
        new_digs.remove(i)
        new_no = ""
        for j in new_digs:
            new_no = new_no + j
        ls = permute(new_no)
        for k in ls:
            permutations.append(k + i)
           
    return permutations
        
    
    
res = permute(no)
res = list(set(res))
res = sorted(res)
for i in res:
    if len(elements(i)) == len(elements(no)):
        print(i)