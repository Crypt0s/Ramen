import re,time

# Stuff that only needs to be instanced once throughout the entire modules use should be here
passwd_regex = re.compile('^.*pass.*=.*$')

# All extensions need a __match__ to see if the attrs match and the module should be run
def __match__(fattrs):
        return True if re.match(r'^.*\.(config|ini|eml)$',fattrs.filename) else False

# All extensions have an action, which is run if the __match__ is true. If you want all matches to be true, you want to write an action, not an extension.
def action(fattrs):
    result_array = []
    with open(fattrs.path) as password_file:
            line = password_file.next()
            while line is not None:
                res = passwd_regex.search(line)
                if res is not None:
                   result_array.append(res.group())
                try:
                    line = password_file.next()
                except:
                    line = None


    # Note here that I am creating a separate file for each file I find passwords in.  This prevents threading issues because it's one thread to one file
    # If you want multiple threads to write to a file, you'll need to implement a file lock system (probably using a file semaphore or reading a named pipe.)
    if len(result_array)>0:
        with open('passwords/'+fattrs.filename+str(time.time()),'w+') as outfile:
            [outfile.write(item) for item in result_array]

# testing the module -- you should have something here
if __name__ == "__main__":
    print ""
    
