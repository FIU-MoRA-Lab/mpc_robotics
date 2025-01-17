import os
# Specify a sorting network, and provide constructors for different instances
# A sorting network is a static structure which specifies a topological order of swaps
# to make to sort a list.
# represented as a list of index tuples to compare and swap if necessary.
# TODO - could group swaps into parallelizable bundles.
class SortingNetwork:
    # types are 'BUBBLE' and 'ODD-EVEN-MERGE'
    def __init__(self, type, n):
        self.swaps = []
        if os.path.exists(type + str(n)):
            file = open(type + str(n), "r")
            for line in file:
                data = line.split()
                self.swaps.append((int(data[0]),int(data[1])))
            file.close() 
        elif type == 'BUBBLE':
            for i in range(n-1):
                for j in range(n-i-1):
                    self.swaps.append((j, j+1))
        elif type == 'ODD-EVEN-MERGE':
            # TODO - make dynamic for n sensors, currently hard-coded for 3
            # top two sensors provide sorted subsequences:
            self.swaps = odd_even_merge_sort(0,n//2, True)
            # bottom sensor is sorted, and it is padded below by max, so already sorted.
            # now merge top and bottom:
            self.swaps.extend(odd_even_merge_sort(0,n, True))
            save_swaps(self.swaps, type + str(n))
        # print(self.swaps)
        
def save_swaps(swaps, filename):
    file = open(filename, "x")
    file.writelines(str(i[0]) + " " + str(i[1]) + "\n" for i in swaps)
    file.close()
# s = SortingNetwork('BUBBLE', 6)
#Batcher algorithm based on C++ implmentation found on:
#https://www.inf.hs-flensburg.de/lang/algorithmen/sortieren/networks/oemen.htm
def odd_even_merge_sort(lo, n, sorted_halves):
    swaps = []
    if n>1:
        m = n//2
        if not(sorted_halves):
            swaps = swaps + odd_even_merge_sort(lo, m, False) + odd_even_merge_sort(lo + m, m, False)
        swaps = swaps + odd_even_merge(lo, n, True)
    return swaps
def odd_even_merge(lo, n, r):
    swaps = []
    m = r*2
    if(m < n):
        swaps = swaps + odd_even_merge(lo, n, m)    # even
        swaps = swaps + odd_even_merge(lo+r, n, m)  # odd
        for i in range(lo+r, lo+n-r, m):
            swaps.append((i,i+r))
    else:
        swaps.append((lo, lo+r))
    return swaps