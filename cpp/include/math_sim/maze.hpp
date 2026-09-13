#pragma once

#include <algorithm>
#include <cstdint>
#include <stdexcept>
#include <vector>

namespace math_sim::maze {

enum Wall : std::uint8_t {
    North = 1u << 0,
    East  = 1u << 1,
    South = 1u << 2,
    West  = 1u << 3,
    AllWalls = North | East | South | West,
};

struct Point { int x = 0; int y = 0; };

struct Cell {
    std::uint8_t walls = AllWalls;
};

struct Maze {
    int width = 0;
    int height = 0;
    std::vector<Cell> cells;

    Maze() = default;
    Maze(int w, int h) : width(w), height(h), cells(static_cast<std::size_t>(w * h)) {
        if (w <= 0 || h <= 0) throw std::invalid_argument("maze dimensions must be positive");
    }

    bool in_bounds(int x, int y) const { return x >= 0 && y >= 0 && x < width && y < height; }
    int index(int x, int y) const { return y * width + x; }

    Cell& at(int x, int y) {
        if (!in_bounds(x, y)) throw std::out_of_range("maze cell out of bounds");
        return cells[static_cast<std::size_t>(index(x, y))];
    }
    const Cell& at(int x, int y) const {
        if (!in_bounds(x, y)) throw std::out_of_range("maze cell out of bounds");
        return cells[static_cast<std::size_t>(index(x, y))];
    }
};

inline std::uint8_t opposite(std::uint8_t wall) {
    if (wall == North) return South;
    if (wall == South) return North;
    if (wall == East) return West;
    if (wall == West) return East;
    throw std::invalid_argument("invalid wall");
}

inline void remove_wall(Maze& m, Point a, Point b) {
    const int dx = b.x - a.x, dy = b.y - a.y;
    std::uint8_t wa = 0;
    if (dx == 1 && dy == 0) wa = East;
    else if (dx == -1 && dy == 0) wa = West;
    else if (dx == 0 && dy == 1) wa = South;
    else if (dx == 0 && dy == -1) wa = North;
    else throw std::invalid_argument("cells must be orthogonal neighbors");
    m.at(a.x, a.y).walls &= static_cast<std::uint8_t>(~wa);
    m.at(b.x, b.y).walls &= static_cast<std::uint8_t>(~opposite(wa));
}

inline bool can_move(const Maze& m, Point p, int dx, int dy) {
    const int nx = p.x + dx, ny = p.y + dy;
    if (!m.in_bounds(nx, ny)) return false;
    std::uint8_t wall = 0;
    if (dx == 1 && dy == 0) wall = East;
    else if (dx == -1 && dy == 0) wall = West;
    else if (dx == 0 && dy == 1) wall = South;
    else if (dx == 0 && dy == -1) wall = North;
    else return false;
    return (m.at(p.x, p.y).walls & wall) == 0;
}

inline std::vector<Point> neighbors(const Maze& m, Point p) {
    std::vector<Point> out;
    if (can_move(m, p, 1, 0)) out.push_back({p.x + 1, p.y});
    if (can_move(m, p, -1, 0)) out.push_back({p.x - 1, p.y});
    if (can_move(m, p, 0, 1)) out.push_back({p.x, p.y + 1});
    if (can_move(m, p, 0, -1)) out.push_back({p.x, p.y - 1});
    return out;
}

} // namespace math_sim::maze
