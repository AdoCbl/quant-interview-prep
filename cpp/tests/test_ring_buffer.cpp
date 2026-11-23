#include <cassert>
#include <cstdio>

#include "ring_buffer.hpp"

int main() {
    SpscRingBuffer<int, 4> rb;
    for (int i = 0; i < 4; ++i) assert(rb.push(i));
    assert(!rb.push(99));  // full
    for (int i = 0; i < 4; ++i) assert(rb.pop() == i);
    assert(!rb.pop());  // empty
    std::puts("ring_buffer: ok");
}
