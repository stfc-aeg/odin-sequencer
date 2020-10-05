provides = ['spi_read', 'spi_write']

def spi_read(num_bytes=1):

    print("Called spi_read for {} bytes".format(num_bytes))
    return list(range(num_bytes))

def spi_write(vals=[0x1]):

    print("Called spi_write for {}".format(vals))
