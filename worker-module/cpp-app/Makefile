CC = g++
CFLAGS = -std=c++11

SDIR=src
ODIR=bin
BDIR=bin

_OBJ = calculator.o
OBJ = $(patsubst %, $(ODIR)/%, $(_OBJ))


$(ODIR)/%.o: $(SDIR)/%.cpp
	$(CC) -c -o $@ $< $(CFLAGS)

calculator: $(OBJ)
	$(CC) -o $(BDIR)/$@ $^ $(CFLAGS)

.PHONY: clean

clean:
	rm -f $(ODIR)/*.o *~ core $(BDIR)/*~ 
