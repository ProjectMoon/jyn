'''
Simple module to demonstrate how to use jyn.
'''
import jyn

lib = jyn.libc()
printf = lib.printf

printf("Hello world! I am printing from Jython!\n")
printf("I will write to a file, and echo to the screen.\n")

printf("Enter something: ")
buf = jyn.Buffer(80)
lib.read(jyn.stdin, buf, buf.size)
enteredText = buf.asString()
printf("echo: %s\n", enteredText)

printf("Now enter a filename: ")
filename = raw_input()

#Make sure to set the return type to Pointer, as the default is int
lib.fopen.restype = jyn.Pointer
ptr = lib.fopen(filename, "w")
lib.fprintf(ptr, enteredText)
lib.fclose(ptr)
