
./autogen.sh
./configure
make -j$(nproc) clean
make -j$(nproc) all
$CXX $CXXFLAGS -std=c++11   -I./include -I.   ./src/tools/ftfuzzer/ftfuzzer.cc -o $OUT/ftfuzzer   ./objs/*.o -lFuzzingEngine   /usr/lib/x86_64-linux-gnu/libarchive.a   ./objs/.libs/libfreetype.a
