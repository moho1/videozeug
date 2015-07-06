cornerpin: cornerpin.cpp
	clang++ -o cornerpin -std=c++14 $$(pkg-config --cflags --libs opencv) -Wall -Ofast -funroll-loops -march=native cornerpin.cpp
