import os
import datetime
import numpy

print(os.path.isfile(os.path.dirname(os.path.abspath(__file__))+"/data/carts/1.json"))

print(str(int(datetime.datetime.utcnow().timestamp()))[-1:-5:-1][::-1])
print(str(int(datetime.datetime.utcnow().timestamp())))
print(str(numpy.base_repr(354546286634074115, base=36))+"_" +
      str(numpy.base_repr(int(datetime.datetime.utcnow().timestamp()), base=36)))
print(int("2OZ063JO2VIB",36))