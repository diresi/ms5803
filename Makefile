CC      = /usr/bin/gcc
CFLAGS  = -Wall

out = crc4

main: crc4.c
	$(CC) $(CFLAGS) -o $(out) crc4.c

clean:
	rm -rf $(out)
