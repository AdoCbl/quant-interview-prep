// Single-producer single-consumer lock-free ring buffer (seed example).
#pragma once
#include <array>
#include <atomic>
#include <cstddef>
#include <optional>

template <typename T, std::size_t N>
class SpscRingBuffer {
    static_assert((N & (N - 1)) == 0, "N must be a power of two");

public:
    bool push(const T& v) {
        auto head = head_.load(std::memory_order_relaxed);
        if (head - tail_.load(std::memory_order_acquire) == N) return false;  // full
        buf_[head & (N - 1)] = v;
        head_.store(head + 1, std::memory_order_release);
        return true;
    }

    std::optional<T> pop() {
        auto tail = tail_.load(std::memory_order_relaxed);
        if (tail == head_.load(std::memory_order_acquire)) return std::nullopt;  // empty
        T v = buf_[tail & (N - 1)];
        tail_.store(tail + 1, std::memory_order_release);
        return v;
    }

private:
    std::array<T, N> buf_{};
    alignas(64) std::atomic<std::size_t> head_{0};
    alignas(64) std::atomic<std::size_t> tail_{0};
};
